from gpt_graph_builder import DirectedGraphBuilder
from run_gpt import OutputFormat, run_gpt
from typing import List, Tuple
import os
import logging
from pathlib import Path
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("classifier")


def save_file(filename, text):
    with open(filename, "w") as text_file:
        text_file.write(text)


def generate_classification_input_graph(input_filename: str,
                                         output_filename: str,
                                         shape_filename_list: List[str],
                                         output_format: OutputFormat) -> Tuple[str, str]:
    """
    Generates a graph XML file and associated properties file for generating a classification composite image for the
    the Random Forest algorithm.  These files can then be executed using GPT to create the input for the Random Forest
    execution graph.
    :param input_filename: the filename of a raster image that the training data will extracted from.  This image
    should have previously been resampled so that all bands are at a common resolution.
    :param shape_filename_list: a list of SHP vector files that contain the polygons used to extract regions of the input
    raster for each class.  Each item in the list should represent a single output class in the data set.
    :param output_filename: the filename that the training data will be saved to
    :return:
    """

    xml = ""
    properties = ""

    graph_builder = DirectedGraphBuilder()

    # Open the 'graph' tag
    xml += graph_builder._get_graph_open_tag()

    # Add an entry in the XML and properties file for the raster image
    _xml, _properties = graph_builder._add_input_node(input_filename)
    xml += _xml
    properties += _properties

    # Add an entry in the XML and properties file for each shape vector
    for _shape_filename in shape_filename_list:
        _xml, _properties = graph_builder._add_import_vector_node(shape_filename=_shape_filename)

        xml += _xml
        properties += _properties

    # Add the output node
    _xml, _properties = graph_builder._add_output_node(output_filename, output_format)
    xml += _xml
    properties += _properties

    # Close the 'graph' tag
    xml += graph_builder._get_graph_close_tag()

    return xml, properties


def train_random_forest(working_dir: str,
                        input_filename: str,
                        output_filename: str,
                        classifier_name: str,
                        feature_bands: List[str],
                        training_vectors: str) -> str:
    assert os.path.isdir(working_dir), "Unable to locate working directory '{}'.".format(working_dir)
    assert os.path.isfile(input_filename), "Input file '{}' was missing.".format(input_filename)

    #   Performs the following functions
    #
    #   1.  Generate the graph and properties file for the classifier
    #   2.  Save the graph and properties files to disk for execution by GPT
    #   3.  Use gpt to execute the graph
    xml_filename = "random_forest.xml"
    xml_file_path = os.path.join(working_dir, xml_filename)

    properties_filename = "random_forest.properties"
    properties_file_path = os.path.join(working_dir, properties_filename)

    #   1.  Generate the graph and properties file for the classifier
    xml, properties = generate_classification_training_graph(input_filename=input_filename,
                                                              output_filename=output_filename,
                                                              classifier_name=classifier_name,
                                                              feature_bands=feature_bands,
                                                              training_vectors=training_vectors,
                                                              output_format=OutputFormat.GEOTIFF)

    #   2.  Save the graph and properties files to disk for execution by GPT
    save_file(xml_file_path, xml)
    assert os.path.isfile(xml_file_path), "Graph xml file '{}' was not found.".format(xml_file_path)

    save_file(properties_file_path, properties)
    assert os.path.isfile(properties_file_path), "Graph xml file '{}' was not found.".format(properties_file_path)
    print("Using xml & properties file {}".format(properties_file_path))

    #   3.  Use gpt to execute the graph
    try:
        run_gpt(input_filename, output_filename, xml_file_path, properties_file_path)
    except:
        logger.exception("Exception was caught whilst training classifier.")
        raise

    output_file_path = Path(output_filename)
    if output_file_path.suffix == "":
        output_file_path = output_file_path.with_suffix(".tif")

    assert os.path.isfile(output_file_path), "Expected output file '{}' was not found.".format(output_file_path)

    return output_file_path


def generate_classification_training_graph(input_filename: str,
                                            output_filename: str,
                                            classifier_name: str,
                                            output_format: OutputFormat,
                                            feature_bands: List[str],
                                            training_vectors: str):
    xml = ""
    properties = ""

    graph_builder = DirectedGraphBuilder()

    # Open the 'graph' tag
    xml += graph_builder._get_graph_open_tag()

    # Add an entry in the XML and properties file for the raster image
    _xml, _properties = graph_builder._add_input_node(input_filename=input_filename)
    xml += _xml
    properties += _properties

    # Add the random forest node
    _xml, _properties = graph_builder._add_random_forest_node(classifier_name=classifier_name,
                                                              feature_bands=feature_bands,
                                                              training_vectors=training_vectors)
    xml += _xml
    properties += _properties

    # Add the output node
    _xml, _properties = graph_builder._add_output_node(output_filename=output_filename,
                                                       output_format=output_format)
    xml += _xml
    properties += _properties

    # Close the 'graph' tag
    xml += graph_builder._get_graph_close_tag()

    return xml, properties


def generate_reproject_graph(input_filename: str,
                              output_filename: str,
                              output_format: OutputFormat,
                              well_known_text: str):
    xml = ""
    properties = ""

    graph_builder = DirectedGraphBuilder()

    # Open the 'graph' tag
    xml += graph_builder._get_graph_open_tag()

    # Add an entry in the XML and properties file for the raster image
    _xml, _properties = graph_builder._add_input_node(input_filename=input_filename)
    xml += _xml
    properties += _properties

    # Add the random forest node
    _xml, _properties = graph_builder._add_reproject_node(well_known_text=well_known_text)
    xml += _xml
    properties += _properties

    # Add the output node
    _xml, _properties = graph_builder._add_output_node(output_filename=output_filename,
                                                       output_format=output_format)
    xml += _xml
    properties += _properties

    # Close the 'graph' tag
    xml += graph_builder._get_graph_close_tag()
    #
    # xml_filename = "/mnt/hgfs/D/nstp/reproject.xml"
    # with open(xml_filename, "w") as xml_file:
    #     xml_file.write(xml)
    #
    # properties_filename = "/mnt/hgfs/D/nstp/reproject.properties"
    # with open(properties_filename, "w") as properties_file:
    #     properties_file.write(properties)

    return xml, properties


def generate_resample_graph(input_filename: str,
                             output_filename: str,
                             output_format: OutputFormat,
                             reference_band: str):
    xml = ""
    properties = ""

    graph_builder = DirectedGraphBuilder()

    # Open the 'graph' tag
    xml += graph_builder._get_graph_open_tag()

    # Add an entry in the XML and properties file for the raster image
    _xml, _properties = graph_builder._add_input_node(input_filename=input_filename)
    xml += _xml
    properties += _properties

    # Add the random forest node
    _xml, _properties = graph_builder._add_resample_node(reference_band=reference_band)
    xml += _xml
    properties += _properties

    # Add the output node
    _xml, _properties = graph_builder._add_output_node(output_filename=output_filename,
                                                       output_format=output_format)
    xml += _xml
    properties += _properties

    # Close the 'graph' tag
    xml += graph_builder._get_graph_close_tag()

    return xml, properties


def generate_subset_graph(input_filename: str,
                           output_filename: str,
                           output_format: OutputFormat,
                           bands: List[str],
                           reference_band: str) -> Tuple[str, str]:
    xml = ""
    properties = ""

    graph_builder = DirectedGraphBuilder()

    # Open the 'graph' tag
    xml += graph_builder._get_graph_open_tag()

    # Add an entry in the XML and properties file for the raster image
    _xml, _properties = graph_builder._add_input_node(input_filename=input_filename)
    xml += _xml
    properties += _properties

    # Add the random forest node
    _xml, _properties = graph_builder._add_subset_node(bands=bands,
                                                       reference_band=reference_band,
                                                       region=None)
    xml += _xml
    properties += _properties

    # Add the output node
    _xml, _properties = graph_builder._add_output_node(output_filename=output_filename,
                                                       output_format=output_format)
    xml += _xml
    properties += _properties

    # Close the 'graph' tag
    xml += graph_builder._get_graph_close_tag()

    return xml, properties
