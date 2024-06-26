#    Copyright 2021 Division of Medical Image Computing, German Cancer Research Center (DKFZ), Heidelberg, Germany
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
from batchgenerators.utilities.file_and_folder_operations import subfiles

from hd_bm.utils import blockPrint, enablePrint

blockPrint()
from nnunet.inference.predict import predict_cases
from nnunet.evaluation.evaluator import evaluate_folder

enablePrint()
import argparse
from hd_bm.paths import folder_with_hd_bm_slim_parameter_files
from hd_bm.prepare_input_args import prepare_input_args_hd_bm_slim
from hd_bm.setup_hd_bm import maybe_download_weights


def main():
    parser = argparse.ArgumentParser(
        description="This script will allow you to run HD-BM (slim) to predict multiple cases with modalities"
        " (with index):\n T1ce (0000), FLAIR (0001)"
        "The different modalities should follow nnUNet naming convention `{SOME_ID}_{ModalityID}.nii.gz`"
        "To predict single cases, please use `hd_bm_slim_predict`"
        "Should you have access to the T1 and T1sub modality please use the `hd_bm_predict` or "
        "`hd_bm_predict_folder` function instead."
    )

    parser.add_argument(
        "-i",
        "--input_folder",
        type=str,
        required=True,
        help="Folder containing input files (no nested folder structure supported). All .nii.gz files in this "
        "folder are attempted to be processed.",
    )
    parser.add_argument(
        "-o",
        "--output_folder",
        type=str,
        required=True,
        help="Output folder. This is where the resulting segmentations will be saved. Cannot be the "
        "same folder as the input folder. If output_folder does not exist it will be created",
    )
    parser.add_argument(
        "-gt",
        "--groundtruth_folder",
        type=str,
        required=True,
        help="Folder containing ground truth segmentations for the input cases provided.",
    )
    parser.add_argument(
        "-p",
        "--processes",
        default=4,
        type=str,
        required=False,
        help="Number of processes for data preprocessing and nifti export. You should not have to "
        "touch this. So don't unless there is a clear indication that it is required. Default: 4",
    )
    parser.add_argument(
        "--keep_existing",
        default=True,
        required=False,
        action="store_false",
        help="Set to False to overwrite segmentations in output_folder. If true continue where you left off "
        "(useful if something crashes). If this flag is not set, all segmentations that may "
        "already be present in output_folder will be kept.",
    )
    parser.add_argument(
        "-mod",
        "--skip_modality_check",
        type=bool,
        required=False,
        default=0,
        help="Optional: Skips asking if the modalities are provided as expected",
        nargs="?",
    )
    parser.add_argument(
        "--verbose",
        required=False,
        default=False,
        action="store_true",
        help="Optional: Skips asking if the modalities are provided as expected",
    )

    args = parser.parse_args()
    input_folder = args.input_folder
    output_folder = args.output_folder
    groundtruth_folder = args.groundtruth_folder
    processes = args.processes
    keep_existing = args.keep_existing
    skip_modality = args.skip_modality_check
    verbose = args.verbose

    maybe_download_weights()

    # we must generate a list of input filenames
    nii_files = subfiles(input_folder, suffix=".nii.gz", join=False)
    unique_ids = list(set([file[:-12] for file in nii_files]))

    input_image_names = []
    output_names = []
    for unique_id in unique_ids:
        input_image_mod_names, output_name = prepare_input_args_hd_bm_slim(
            input_dir=input_folder,
            input_id=unique_id,
            output_dir=output_folder,
            output_id=None,
            skip_modality_confirmation=skip_modality,
        )
        input_image_names.append(input_image_mod_names)
        output_names.append(output_name)

    if verbose:
        print("Predicting cases. This may take a while ...")
        blockPrint()
    predict_cases(
        model=folder_with_hd_bm_slim_parameter_files,
        list_of_lists=input_image_names,
        output_filenames=output_names,
        folds=(0, 1, 2, 3, 4),
        save_npz=False,
        num_threads_preprocessing=processes,
        num_threads_nifti_save=processes,
        segs_from_prev_stage=None,
        do_tta=True,
        mixed_precision=None,
        overwrite_existing=not keep_existing,
        all_in_gpu=False,
    )

    enablePrint()
    print("Evaluating the results ...")
    evaluate_folder(output_folder, groundtruth_folder, labels=(1, 2))
    print("Finished predicting and evaluating HD-BM Slim.\n Exiting.")


if __name__ == "__main__":
    main()
