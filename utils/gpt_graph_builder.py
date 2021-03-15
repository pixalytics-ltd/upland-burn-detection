import os
import textwrap
from pathlib import Path
from typing import Tuple, List
from run_gpt import OutputFormat, _output_format_lookup


class DirectedGraphBuilder:
    def __init__(self):
        self._import_node_id = 0
        self.source_node = None

    def _add_input_node(self,
                        input_filename: str) -> Tuple[str, str]:
        """
        Adds the input source file to the DAG.
        :param input_filename: the file that will be used as input to the processing graph
        :return: a tuple consisting of (the name of the input node, xml for the input node, properties for the input node)
        """
        assert os.path.isfile(input_filename), "Unable to find input file '{}'.".format(input_filename)
        node_id = "Read"

        #   xml for the read operation.  The graph will reference a variable in the properties file to enable easy
        #   reuse of the graph elsewhere
        _xml = """\
        <node id="{n_id}">
          <operator>Read</operator>
            <sources/>
            <parameters class="com.bc.ceres.binding.dom.XppDomElement">
            <file>${{source_image}}</file>
          </parameters>
        </node>
        """.format(n_id=node_id)

        #   add an entry to the properties file for the input filename placeholder
        _properties = """\
        source_image={fname}
        """.format(fname=input_filename)

        #   source of next node will be this node
        self.source_node = node_id
        return textwrap.dedent(_xml), textwrap.dedent(_properties)

    def _add_output_node(self,
                         output_filename: str,
                         output_format: OutputFormat = OutputFormat.DIMAP) -> Tuple[str, str]:
        node_id = "Write"

        #   get information about the requested output format
        format_name, format_extension = _output_format_lookup[output_format]
        print("Using {} for {}".format(output_format, output_filename))
    
        #   make sure the output has the correct extension
        output_path = Path(output_filename)
        output_path = output_path.with_suffix(format_extension)

        #   xml for the write operation.  The graph will reference a variable in the properties file to enable easy
        #   reuse of the graph elsewhere
        _xml = """\
        <node id="{n_id}">
          <operator>Write</operator>
          <sources>
            <sourceProduct refid="{src}"/>
          </sources>
          <parameters class="com.bc.ceres.binding.dom.XppDomElement">
            <file>${{output_filename}}</file>
            <formatName>${{output_format}}</formatName>
          </parameters>
        </node>
        """.format(n_id=node_id, src=self.source_node)

        #   add an entry to the properties file for the output filename placeholder
        _properties = """\
        output_filename={fname}
        output_format={fmt}
        """.format(fname=output_path, fmt=format_name)

        return textwrap.dedent(_xml), textwrap.dedent(_properties)

    @staticmethod
    def _get_graph_open_tag() -> str:
        xml = """\
        <graph id="Graph">
          <version>1.0</version>
        """
        return textwrap.dedent(xml)

    @staticmethod
    def _get_graph_close_tag() -> str:
        xml = """\
        </graph>
        """
        return textwrap.dedent(xml)

    def _add_import_vector_node(self,
                                shape_filename: str) -> [str, str]:
        assert os.path.isfile(shape_filename)

        node_identifier = "Import-Vector-{n}".format(n=self._import_node_id)
        file_identifier = "shapefile_{n}".format(n=self._import_node_id)
        self._import_node_id += 1

        _xml = """\
        <node id="{n_id}">
          <operator>Import-Vector</operator>
            <sources>
              <sourceProduct refid="{src}"/>
            </sources>
            <parameters class="com.bc.ceres.binding.dom.XppDomElement">
              <vectorFile>${{{id}}}</vectorFile>
            <separateShapes>false</separateShapes>
          </parameters>
        </node>
        """.format(n_id=node_identifier, src=self.source_node, id=file_identifier)

        properties = """\
        {id}={fname}
        """.format(id=file_identifier, fname=shape_filename)

        #   source of next node will be this node
        self.source_node = node_identifier
        return textwrap.dedent(_xml), textwrap.dedent(properties)

    def _add_random_forest_node(self,
                                classifier_name: str,
                                training_vectors: str,
                                feature_bands: List[str]) -> Tuple[str, str]:
        node_id = "Random-Forest-Classifier"
        feature_bands = ",".join(feature_bands).upper()

        tree_count = 10
        train_samples = 5000
        classifier_name = classifier_name
        #training_vectors = "Artificial,Grassland,Managed Vegetation,Shrub Cover,TreeCover"
        #feature_bands = "B2,B3,B4,B5,B6,B8,B8A"

        _xml = """\
        <node id="{n_id}">
          <operator>Random-Forest-Classifier</operator>
          <sources>
            <sourceProduct refid="{src}"/>
          </sources>
          <parameters class="com.bc.ceres.binding.dom.XppDomElement">
            <treeCount>{t_count}</treeCount>
            <numTrainSamples>{t_samples}</numTrainSamples>
            <savedClassifierName>{name}</savedClassifierName>
            <doLoadClassifier>false</doLoadClassifier>
            <doClassValQuantization>true</doClassValQuantization>
            <minClassValue>0.0</minClassValue>
            <classValStepSize>5.0</classValStepSize>
            <classLevels>101</classLevels>
            <trainOnRaster>false</trainOnRaster>
            <trainingBands/>
            <trainingVectors>{t_vec}</trainingVectors>
            <featureBands>{bands}</featureBands>
            <labelSource>VectorNodeName</labelSource>
            <evaluateClassifier>false</evaluateClassifier>
            <evaluateFeaturePowerSet>false</evaluateFeaturePowerSet>
            <minPowerSetSize>2</minPowerSetSize>
            <maxPowerSetSize>7</maxPowerSetSize>
            </parameters>
          </node>
        """.format(n_id=node_id,
                   src=self.source_node,
                   t_count=tree_count,
                   t_samples=train_samples,
                   name=classifier_name,
                   t_vec=training_vectors,
                   bands=feature_bands)

        #   source of next node will be this node
        self.source_node = node_id
        return _xml, ""

    def _add_reproject_node(self,
                            well_known_text: str):
        node_id = "Reproject"

        _xml = """\
        <node id="{n_id}">
            <operator>Reproject</operator>
            <sources>
                <sourceProduct refid="Read"/>
            </sources>
            <parameters class="com.bc.ceres.binding.dom.XppDomElement">
              <wktFile/>
              <crs>{crs}
              </crs>
              <resampling>Nearest</resampling>
              <referencePixelX/>
              <referencePixelY/>
              <easting/>
              <northing/>
              <orientation/>
              <pixelSizeX/>
              <pixelSizeY/>
              <width/>
              <height/>
              <tileSizeX/>
              <tileSizeY/>
              <orthorectify>false</orthorectify>
              <elevationModelName/>
              <noDataValue>NaN</noDataValue>
              <includeTiePointGrids>true</includeTiePointGrids>
              <addDeltaBands>false</addDeltaBands>
            </parameters>
        </node>
        """.format(n_id=node_id, crs=well_known_text)

        self.source_node = node_id
        return textwrap.dedent(_xml), ""

    def _add_resample_node(self, reference_band: str):
        node_id = "Resample"

        _xml = """\
        <node id="{n_id}">
        <operator>Resample</operator>
        <sources>
          <sourceProduct refid="{src}"/>
        </sources>
        <parameters class="com.bc.ceres.binding.dom.XppDomElement">
          <referenceBand>${{reference_band}}</referenceBand>
          <targetWidth/>
          <targetHeight/>
          <targetResolution/>
          <upsampling>Nearest</upsampling>
          <downsampling>First</downsampling>
          <flagDownsampling>First</flagDownsampling>
          <resamplingPreset/>
          <bandResamplings/>
          <resampleOnPyramidLevels>true</resampleOnPyramidLevels>
        </parameters>
        </node>
        """.format(n_id=node_id, src=self.source_node)

        properties = """\
        reference_band={band}
        """.format(band=reference_band)

        self.source_node = node_id
        return textwrap.dedent(_xml), textwrap.dedent(properties)

    def _add_subset_node(self,
                         bands: List[str],
                         reference_band: str,
                         region=None):
        node_id = "Subset"

        src_bands_str = ",".join(bands).upper()
        reference_band = reference_band.upper()

        _xml = """\
        <node id="{n_id}">
            <operator>Subset</operator>
            <sources>
              <sourceProduct refid="{src}"/>
            </sources>
            <parameters class="com.bc.ceres.binding.dom.XppDomElement">
              <sourceBands>${{source_bands}}</sourceBands>
              <!--<region>0,0,10980,10980</region>-->
              <referenceBand>${{reference_band}}</referenceBand>
              <geoRegion/>
              <subSamplingX>1</subSamplingX>
              <subSamplingY>1</subSamplingY>
              <fullSwath>false</fullSwath>
              <tiePointGridNames/>
              <copyMetadata>true</copyMetadata>
            </parameters>
        </node>
        """.format(n_id=node_id, src=self.source_node)

        properties = """\
        source_bands={src_bands}
        reference_band={ref_band}
        """.format(src_bands=src_bands_str, ref_band=reference_band)

        self.source_node = node_id
        return textwrap.dedent(_xml), textwrap.dedent(properties)
