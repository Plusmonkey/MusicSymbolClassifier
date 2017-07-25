import argparse
import os
from glob import glob
from xml.etree import ElementTree

from PIL import Image
import json

from datasets.AudiverisOmrSymbol import AudiverisOmrSymbol
from datasets.ExportPath import ExportPath


class AudiverisOmrImageGenerator:
    def __init__(self) -> None:
        super().__init__()
        path_of_this_file = os.path.dirname(os.path.realpath(__file__))
        # This mapping contains the relation between the names of the classes used in the Audiveris OMR-dataset
        # annotations and the names that were used for the other datasets
        with open(os.path.join(path_of_this_file,"AudiverisOmrSymbolNameMapping.json")) as file:
            self.symbol_name_mapping = json.load(file)

        # Ledger lines can not be distinguished from tenuto or whole-half-rest, so we ignore it for now
        # For now, we ignore half/full notes, flags and stems too
        with open(os.path.join(path_of_this_file,"AudiverisOmrIgnoredClasses.json")) as file:
            self.ignored_classes = json.load(file)

    def extract_symbols(self, raw_data_directory: str, destination_directory: str):
        """
        Extracts the symbols from the raw XML documents and matching images of the Audiveris OMR dataset into
        individual symbols

        :param raw_data_directory: The directory, that contains the xml-files and matching images
        :param destination_directory: The directory, in which the symbols should be generated into. One sub-folder per
                                      symbol category will be generated automatically
        """
        print("Extracting Symbols from Audiveris OMR Dataset...")

        all_xml_files = [y for x in os.walk(raw_data_directory) for y in glob(os.path.join(x[0], '*.xml'))]
        all_image_files = [y for x in os.walk(raw_data_directory) for y in glob(os.path.join(x[0], '*.png'))]

        data_pairs = []
        for i in range(len(all_xml_files)):
            data_pairs.append((all_xml_files[i], all_image_files[i]))

        for data_pair in data_pairs:
            self.__extract_symbols(data_pair[0], data_pair[1], destination_directory)

    def __extract_symbols(self, xml_file: str, image_file: str, destination_directory: str):
        # xml_file, image_file = 'data/audiveris_omr_raw\\IMSLP06053p1.xml', 'data/audiveris_omr_raw\\IMSLP06053p1.png'
        # xml_file, image_file = 'data/audiveris_omr_raw\\mops-1.xml', 'data/audiveris_omr_raw\\mops-1.png'
        # xml_file, image_file = 'data/audiveris_omr_raw\\mtest1-1.xml', 'data/audiveris_omr_raw\\mtest1-1.png'
        # xml_file, image_file = 'data/audiveris_omr_raw\\mtest2-1.xml', 'data/audiveris_omr_raw\\mtest2-1.png'
        image = Image.open(image_file)
        annotations = ElementTree.parse(xml_file).getroot()
        xml_symbols = annotations.findall("Symbol")

        file_name_without_extension = os.path.splitext(os.path.basename(xml_file))[0]
        symbols = []

        for xml_symbol in xml_symbols:
            symbol_class = xml_symbol.get("shape")

            if symbol_class in self.ignored_classes:
                continue  # Ignored classes will be skipped

            mapped_symbol_class = self.symbol_name_mapping[symbol_class]

            bounds = xml_symbol.find("Bounds")
            x, y, width, height = bounds.get("x"), bounds.get("y"), bounds.get("w"), bounds.get("h")
            x, y, width, height = int(float(x)), int(float(y)), int(float(width)), int(float(height))

            symbol = AudiverisOmrSymbol(mapped_symbol_class, x, y, width, height)
            symbols.append(symbol)

        symbol_number = 0
        for symbol in symbols:
            symbol_class = symbol.symbol_class
            bounding_box_with_one_pixel_margin = symbol.as_bounding_box_with_margin(1)
            symbol_image = image.crop(bounding_box_with_one_pixel_margin)

            target_directory = os.path.join(destination_directory, symbol_class)
            os.makedirs(target_directory, exist_ok=True)

            export_path = ExportPath(destination_directory, symbol_class,
                                     file_name_without_extension + str(symbol_number))
            symbol_image.save(export_path.get_full_path())
            symbol_number += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw_dataset_directory",
        type=str,
        default="../data/audiveris_omr_raw",
        help="The directory, where the raw Audiveris OMR dataset can be found")
    parser.add_argument(
        "--image_dataset_directory",
        type=str,
        default="../data/images",
        help="The directory, where the generated bitmaps will be created")

    flags, unparsed = parser.parse_known_args()

    audiveris_omr_image_generator = AudiverisOmrImageGenerator()
    audiveris_omr_image_generator.extract_symbols(flags.raw_dataset_directory, flags.image_dataset_directory)