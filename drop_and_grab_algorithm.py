from qgis.core import (QgsProcessingParameterFile)
from qgis import processing
from .qscout_pin_algorithm import *
from .pin_dropper_algorithm import *
from .grid_aggregator_algorithm import *
from .value_grabber_algorithm import QScoutValueGrabberAlgorithm, band_field


class DropAndGrabAlgoithm(QScoutPinDropperAlgorithm, QScoutValueGrabberAlgorithm, QScoutGridAggregatorAlgorithm):

    DROP_AND_GRAB_GRID_OUT = 'DROP_AND_GRAB_GRID_OUT'
    DROP_AND_GRAB_POINTS_OUT = 'DROP_AND_GRAB_POINTS_OUT'

    def initAlgorithm(self, config):
        # QSCOUT PIN ALGORITHM PARAMS

        # raster layer. repeating pattern in the raster will be used to drop pins
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                QScoutPinAlgorithm.TARGETING_RASTER_INPUT,
                self.tr('Targeting Raster'),
                [QgsProcessing.TypeRaster],
                optional=True
            )
        )
        # bounding box
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                QScoutPinAlgorithm.BOUND_BOX_INPUT,
                self.tr('Bounding Box'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        # direction vector for rows
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                QScoutPinAlgorithm.ROW_VECTOR_INPUT,
                self.tr('Row Vector'),
                [QgsProcessing.TypeVectorLine],
            )
        )

        # rating function
        param = QgsProcessingParameterEnum(
            QScoutPinAlgorithm.RATE_OFFSET_MATCH_FUNCTION_INPUT,
            self.tr("Rate Offset Match Function"),
            options=MATCH_FUNCTIONS,
            defaultValue=0  # nothing I write here makes any difference
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # whether to compare from root
        param = QgsProcessingParameterBoolean(
            QScoutPinAlgorithm.COMPARE_FROM_ROOT_INPUT,
            self.tr("Compare from Root"),
            defaultValue=False
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # row height
        self.addParameter(
            QgsProcessingParameterDistance(
                QScoutPinAlgorithm.ROW_SPACING_INPUT,
                self.tr('Row Spacing'),
                parentParameterName=QScoutPinAlgorithm.BOUND_BOX_INPUT,
                minValue=0
            )
        )

        # point interval
        self.addParameter(
            QgsProcessingParameterDistance(
                QScoutPinAlgorithm.POINT_INTERVAL_INPUT,
                self.tr('Point Interval'),
                parentParameterName=QScoutPinAlgorithm.BOUND_BOX_INPUT,
                minValue=0
            )
        )

        # overlay box radius
        param = QgsProcessingParameterNumber(
            QScoutPinAlgorithm.OVERLAY_BOX_RADIUS_INPUT,
            self.tr('Overlay Box Radius'),
            type=QgsProcessingParameterNumber.Integer,
            minValue=0,
            defaultValue=2
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # match threshold
        self.addParameter(
            QgsProcessingParameterNumber(
                QScoutPinAlgorithm.OVERLAY_MATCH_THRESHOLD_INPUT,
                self.tr("Match Threshold"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=.85,  # this number has absolutely no scientific or mathematical basis
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                QScoutPinAlgorithm.START_CORNER_INPUT,
                self.tr("Start Corner"),
                options=START_CORNERS,
                defaultValue=0
            )
        )

        # patch size
        param = QgsProcessingParameterNumber(
            QScoutPinAlgorithm.PATCH_SIZE_INPUT,
            self.tr('Maximum Patch Size'),
            type=QgsProcessingParameterNumber.Integer,
            minValue=0,
            defaultValue=2
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # optional parameters
        param = QgsProcessingParameterNumber(
            QScoutPinAlgorithm.ROW_SPACING_STDEV_INPUT,
            self.tr('Row Spacing Stdev'),
            type=QgsProcessingParameterNumber.Double,
            minValue=0,
            optional=True
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # patch size
        param = QgsProcessingParameterNumber(
            QScoutPinAlgorithm.POINT_INTERVAL_STDEV_INPUT,
            self.tr('Point Interval Stdev'),
            type=QgsProcessingParameterNumber.Double,
            minValue=0,
            optional=True
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # search iteration size
        param = QgsProcessingParameterNumber(
            QScoutPinAlgorithm.SEARCH_ITERATION_SIZE_INPUT,
            self.tr("Search Iteration Size"),
            type=QgsProcessingParameterNumber.Integer,
            minValue=2,
            defaultValue=5
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # number of search iteGridAggregatorAlgorithmrations
        param = QgsProcessingParameterNumber(
            QScoutPinAlgorithm.SEARCH_NUM_ITERATIONS_INPUT,
            self.tr("Number of Search Iterations"),
            type=QgsProcessingParameterNumber.Integer,
            minValue=1,
            defaultValue=2
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # precision bias coefficient
        param = QgsProcessingParameterNumber(
            QScoutPinAlgorithm.PRECISION_BIAS_COEFFICIENT_INPUT,
            self.tr("Precision Bias Coefficient"),
            type=QgsProcessingParameterNumber.Double,
            minValue=0,
            defaultValue=0

        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # PIN DROPPER PARAMS
        # fields to use
        param = QgsProcessingParameterString(
            QScoutPinDropperAlgorithm.DATA_SOURCE_FIELDS_TO_USE,
            self.tr("Fields to Use"),
            optional=True
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # panel size
        param = QgsProcessingParameterNumber(
            QScoutPinDropperAlgorithm.PANEL_SIZE_INPUT,
            self.tr("Panel Size"),
            minValue=0,
            defaultValue=0
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # drop data-less points
        self.addParameter(
            QgsProcessingParameterBoolean(
                QScoutPinDropperAlgorithm.DROP_DATALESS_POINTS_INPUT,
                self.tr("Drop Data-less Points"),
                defaultValue=False  # should maybe change to false in production version
            )
        )

        # input data
        self.addParameter(
            QgsProcessingParameterFile(
                QScoutPinDropperAlgorithm.DATA_SOURCE_INPUT,
                self.tr("Input Data"),
                optional=True
            )
        )

        # VALUE GRABBER PARAMS
        # have to use QgsProcessingParameterFile to account for rasters too large to load in qgis
        self.addParameter(
            QgsProcessingParameterFile(
                QScoutValueGrabberAlgorithm.RASTER_INPUT,
                self.tr("Raster File Input")
            )
        )

        # GRID AGGREGATOR PARAMS

        self.addParameter(
            QgsProcessingParameterDistance(
                QScoutGridAggregatorAlgorithm.GRID_CELL_W_INPUT,
                self.tr("Grid Cell Width"),
                parentParameterName=QScoutPinAlgorithm.BOUND_BOX_INPUT,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                QScoutGridAggregatorAlgorithm.GRID_CELL_H_INPUT,
                self.tr("Grid Cell Height"),
                parentParameterName=QScoutPinAlgorithm.BOUND_BOX_INPUT,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                QScoutGridAggregatorAlgorithm.AGGREGATION_FUNCTION_INPUT,
                self.tr("Aggregation Function"),
                options=AGGREGATION_FUNCTIONS,
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.DROP_AND_GRAB_POINTS_OUT,
                self.tr("Points Output")
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.DROP_AND_GRAB_GRID_OUT,
                self.tr("Aggregate Grid")
            )
        )


    # def processAlgorithm(self, parameters, context, feedback):
    #     # QSCOUT PARAMETERS
    #     # required parameters
    #     target_raster = self.parameterAsRasterLayer(parameters, QScoutPinAlgorithm.TARGETING_RASTER_INPUT, context)
    #     bound_box_layer = self.parameterAsVectorLayer(parameters, QScoutPinAlgorithm.BOUND_BOX_INPUT, context)
    #     overlay_box_radius = self.parameterAsDouble(parameters, QScoutPinAlgorithm.OVERLAY_BOX_RADIUS_INPUT, context)
    #     col_w = self.parameterAsDouble(parameters, QScoutPinAlgorithm.POINT_INTERVAL_INPUT, context)
    #     row_h = self.parameterAsDouble(parameters, QScoutPinAlgorithm.ROW_SPACING_INPUT, context)
    #     row_vector_layer = self.parameterAsVectorLayer(parameters, QScoutPinAlgorithm.ROW_VECTOR_INPUT, context)
    #
    #     # optional parameters
    #     row_h_stdev = self.parameterAsDouble(parameters, QScoutPinAlgorithm.ROW_SPACING_STDEV_INPUT, context)
    #     point_interval_stdev = self.parameterAsDouble(parameters, QScoutPinAlgorithm.POINT_INTERVAL_STDEV_INPUT, context)
    #     overlay_match_min_threshold = self.parameterAsDouble(parameters, QScoutPinAlgorithm.OVERLAY_MATCH_THRESHOLD_INPUT,
    #                                                               context)
    #     search_iter_count = self.parameterAsInt(parameters, QScoutPinAlgorithm.SEARCH_NUM_ITERATIONS_INPUT, context)
    #     search_iter_size = self.parameterAsInt(parameters, QScoutPinAlgorithm.SEARCH_ITERATION_SIZE_INPUT, context)
    #     patch_size = self.parameterAsInt(parameters, QScoutPinAlgorithm.PATCH_SIZE_INPUT, context)
    #     offset_func_idx = self.parameterAsEnum(parameters, QScoutPinAlgorithm.RATE_OFFSET_MATCH_FUNCTION_INPUT, context)
    #     compare_from_root = self.parameterAsBool(parameters, QScoutPinAlgorithm.COMPARE_FROM_ROOT_INPUT, context)
    #     precision_bias_coeff = self.parameterAsDouble(parameters, QScoutPinAlgorithm.PRECISION_BIAS_COEFFICIENT_INPUT, context)
    #
    #     start_corner = self.parameterAsEnum(parameters, QScoutPinAlgorithm.START_CORNER_INPUT, context)
    #
    #     # PIN DROPPER PARAMS
    #     data_source = self.parameterAsFile(parameters, QScoutPinDropperAlgorithm.DATA_SOURCE_INPUT, context)
    #     drop_dataless_points = self.parameterAsBool(parameters, QScoutPinDropperAlgorithm.DROP_DATALESS_POINTS_INPUT, context)
    #     fields_to_use = self.parameterAsString(parameters, QScoutPinDropperAlgorithm.DATA_SOURCE_FIELDS_TO_USE, context)
    #     panel_size = self.parameterAsInt(parameters, QScoutPinDropperAlgorithm.PANEL_SIZE_INPUT, context)
    #
    #     pin_dropper_alg_params = {
    #         QScoutPinAlgorithm.TARGETING_RASTER_INPUT: target_raster,
    #         QScoutPinAlgorithm.BOUND_BOX_INPUT: bound_box_layer,
    #         QScoutPinAlgorithm.OVERLAY_BOX_RADIUS_INPUT: overlay_box_radius,
    #         QScoutPinAlgorithm.POINT_INTERVAL_INPUT: col_w,
    #         QScoutPinAlgorithm.ROW_SPACING_INPUT: row_h,
    #         QScoutPinAlgorithm.ROW_VECTOR_INPUT: row_vector_layer,
    #         QScoutPinAlgorithm.ROW_SPACING_STDEV_INPUT: row_h_stdev,
    #         QScoutPinAlgorithm.POINT_INTERVAL_STDEV_INPUT: point_interval_stdev,
    #         QScoutPinAlgorithm.OVERLAY_MATCH_THRESHOLD_INPUT: overlay_match_min_threshold,
    #         QScoutPinAlgorithm.SEARCH_NUM_ITERATIONS_INPUT: search_iter_count,
    #         QScoutPinAlgorithm.SEARCH_ITERATION_SIZE_INPUT: search_iter_size,
    #         QScoutPinAlgorithm.PATCH_SIZE_INPUT: patch_size,
    #         QScoutPinAlgorithm.RATE_OFFSET_MATCH_FUNCTION_INPUT: offset_func_idx,
    #         QScoutPinAlgorithm.COMPARE_FROM_ROOT_INPUT: compare_from_root,
    #         QScoutPinAlgorithm.PRECISION_BIAS_COEFFICIENT_INPUT: precision_bias_coeff,
    #         QScoutPinAlgorithm.START_CORNER_INPUT: start_corner,
    #         QScoutPinDropperAlgorithm.DATA_SOURCE_INPUT: data_source,
    #         QScoutPinDropperAlgorithm.DROP_DATALESS_POINTS_INPUT: drop_dataless_points,
    #         QScoutPinDropperAlgorithm.DATA_SOURCE_FIELDS_TO_USE: fields_to_use,
    #         QScoutPinDropperAlgorithm.PANEL_SIZE_INPUT: panel_size,
    #         QScoutPinDropperAlgorithm.DROPPED_PINS_OUTPUT: "memory:"  # I promise I read this somewhere
    #     }
    #
    #     parameters[QScoutPinDropperAlgorithm.DROPPED_PINS_OUTPUT] = "memory:"
    #
    #     pin_drop_out = QScoutPinDropperAlgorithm.processAlgorithm(self, parameters, context, feedback)
    #     pin_drop_out = pin_drop_out[QScoutPinDropperAlgorithm.DROPPED_PINS_OUTPUT]
    #
    #     vals_raster = self.parameterAsFile(parameters, QScoutValueGrabberAlgorithm.RASTER_INPUT, context)
    #     val_grab_pins = pin_drop_out[QScoutPinDropperAlgorithm.DROPPED_PINS_OUTPUT]
    #
    #     # VALUE GRABBER PARAMS
    #     grab_alg_params = {
    #         QScoutValueGrabberAlgorithm.RASTER_INPUT: vals_raster,
    #         QScoutValueGrabberAlgorithm.POINTS_INPUT: val_grab_pins,
    #         QScoutValueGrabberAlgorithm.POINTS_WITH_VALUES_OUTPUT: "memory:"
    #     }
    #
    #     parameters[QScoutValueGrabberAlgorithm.POINTS_WITH_VALUES_OUTPUT] = "memory:"
    #
    #     grab_alg_out = QScoutValueGrabberAlgorithm.processAlgorithm(self, parameters, context, feedback)
    #     grab_alg_out = grab_alg_out[QScoutValueGrabberAlgorithm.POINTS_WITH_VALUES_OUTPUT]
    #
    #     # GRID AGGREGATOR PARAMS
    #     grid_w = self.parameterAsDouble(parameters, QScoutGridAggregatorAlgorithm.GRID_CELL_W_INPUT, context)
    #     grid_h = self.parameterAsDouble(parameters, QScoutGridAggregatorAlgorithm.GRID_CELL_H_INPUT, context)
    #     ag_idx = self.parameterAsEnum(parameters, QScoutGridAggregatorAlgorithm.AGGREGATION_FUNCTION_INPUT, context)
    #
    #     grabbed_points = grab_alg_out[QScoutValueGrabberAlgorithm.POINTS_WITH_VALUES_OUTPUT]
    #     points_out, points_out_id = self.parameterAsSink(
    #         parameters,
    #         self.DROP_AND_GRAB_POINTS_OUT,
    #         context,
    #         fields=grabbed_points.fields(),
    #         geometryType=QgsWkbTypes.Point,
    #         crs=grabbed_points.crs(),
    #         sinkFlags=QgsFeatureSink.RegeneratePrimaryKey
    #     )
    #
    #     for feature in grabbed_points.getFeatures():
    #         points_out.addFeature(feature)
    #
    #     # this is a bit wonky
    #     fields_to_use_list = map(lambda f: f.strip(), fields_to_use.split(","))
    #     ag_fields = grabbed_points.fields()
    #     regexes = "|".join(map(lambda r: "(%s)" % r, [ROW_REGEX, COL_REGEX, VINE_REGEX, PANEL_REGEX]))
    #     ag_fields = filter(lambda f:
    #                        (not fields_to_use or f.name() in fields_to_use_list)
    #                        and not re.match(regexes, f.name())
    #                        and (f.type() == QVariant.Int or f.type() == QVariant.Double),
    #                        ag_fields)
    #     ag_fields = map(lambda f: f.name(), ag_fields)
    #
    #     grid_ag_alg_params = {
    #         QScoutValueGrabberAlgorithm.POINTS_INPUT: grabbed_points,
    #         QScoutGridAggregatorAlgorithm.GRID_CELL_W_INPUT: grid_w,
    #         QScoutGridAggregatorAlgorithm.GRID_CELL_H_INPUT: grid_h,
    #         QScoutGridAggregatorAlgorithm.AGGREGATION_FUNCTION_INPUT: ag_idx,
    #         QScoutGridAggregatorAlgorithm.FIELDS_TO_USE_INPUT: ag_fields,
    #         QScoutGridAggregatorAlgorithm.AGGREGATE_GRID_OUTPUT: "memory:"
    #     }
    #
    #     parameters[QScoutGridAggregatorAlgorithm.AGGREGATE_GRID_OUTPUT] = "memory:"
    #
    #     grid_alg_out = QScoutGridAggregatorAlgorithm.processAlgorithm(self, parameters, context, feedback)
    #
    #     ag_layer = grid_alg_out[QScoutGridAggregatorAlgorithm.AGGREGATE_GRID_OUTPUT]
    #     grid_out, grid_out_id = self.parameterAsSink(
    #         parameters,
    #         self.DROP_AND_GRAB_GRID_OUT,
    #         context,
    #         fields=ag_layer.fields(),
    #         geometryType=QgsWkbTypes.Polygon,
    #         crs=ag_layer.crs(),
    #         sinkFlags=QgsFeatureSink.RegeneratePrimaryKey
    #     )
    #     for feature in ag_layer.getFeatures():
    #         grid_out.addFeature(feature)
    #
    #     return {self.DROP_AND_GRAB_POINTS_OUT: points_out_id, self.DROP_AND_GRAB_GRID_OUT: grid_out_id}

    def processAlgorithm(self, parameters, context, feedback):
        fields_to_use = self.parameterAsString(parameters, QScoutPinDropperAlgorithm.DATA_SOURCE_FIELDS_TO_USE, context)

        # QScoutPinDropperAlgorithm should find input layer correctly
        # set up empty list to buffer output points from QScoutPinDropperAlgorithm
        self.output_sink = []
        self.extra_sink = None
        QScoutPinDropperAlgorithm.processAlgorithm(self, parameters, context, feedback)
        self.input_buffer = self.output_sink  # set output buffer as input for QScoutValueGrabberAlgorithm
        self.output_sink = None  # create a layer this time
        self.extra_sink = []  # to be read by aggregator
        points_out_id = QScoutValueGrabberAlgorithm.processAlgorithm(self, parameters, context, feedback)[self.POINTS_WITH_VALUES_OUTPUT]

        # this is a bit wonky
        fields_to_use_list = map(lambda f: f.strip(), fields_to_use.split(","))
        # at this point, self.output_sink is the QgsFeatureSink created by QScoutValueGrabberAlgorthm.processAlgorithm
        ag_fields = self.output_sink.fields()
        regexes = "|".join(map(lambda r: "(%s)" % r, [ROW_REGEX, COL_REGEX, VINE_REGEX, PANEL_REGEX]))
        ag_fields = filter(lambda f:
                           (not fields_to_use or f.name() in fields_to_use_list)
                           and not re.match(regexes, f.name())
                           and (f.type() == QVariant.Int or f.type() == QVariant.Double),
                           ag_fields)
        ag_fields = map(lambda f: f.name(), ag_fields)
        parameters[QScoutGridAggregatorAlgorithm.FIELDS_TO_USE_INPUT] = ag_fields  # how will grid aggregator actually handle this? we will find out.

        self.input_buffer = self.extra_sink
        self.output_sink = None
        self.extra_sink = None  # don't waste memory
        grid_out_id = QScoutGridAggregatorAlgorithm.processAlgorithm(self, parameters, context, feedback)[self.AGGREGATE_GRID_OUTPUT]

        return {self.DROP_AND_GRAB_POINTS_OUT: points_out_id, self.DROP_AND_GRAB_GRID_OUT: grid_out_id}

    def add_pin_to_output(self, pin, data, count):
        """
        adds QgsPoint geometry to OUTPUT (feautre sink)
        @param pin an instance of PinDropperPin for this pin
        @param data the row of data from the input data for this pin (or generated)
        @param count the number of features in the sink so far. used for assigning IDs
        @return count incremented by 1
        """
        feat = QgsFeature(id=count)
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(*pin.geoCoords())))
        feat.setAttributes(data)
        self.dropped_pin_features.append(feat)
        return count + 1

    def add_val_grabbed_pin_to_output(self, pin, count):
        self.val_grabbed_pins.append(pin)
        self.pin_sink.addFeature(pin)
        return count + 1

    def pin_feature_source(self):
        return self.dropped_pin_features

    def name(self):
        return "dropandgrab"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Drop Pins and Grid Grab")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("QScout")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'qscout'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DropAndGrabAlgoithm()

    @abstractmethod
    def feature_input(self):
        """
        should return an iterable, generally either a QgsFeatureIterator or list
        """
        return self.input_buffer

    @abstractmethod
    def feature_output(self):
        """
        should return an instance of either QgsFeatureSink or list
        """
        return self.output_sink

    def append_to_feature_output(self, feat, count=0):
        if self.extra_sink is not None:
            self.extra_sink.append(feat)
        return super().append_to_feature_output(feat, count)