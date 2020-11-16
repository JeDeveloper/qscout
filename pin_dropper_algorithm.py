# -*- coding: utf-8 -*-

"""
/***************************************************************************
 pin_dropper
                                 A QGIS plugin
 Drops pins
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-09-29
        copyright            : (C) 2020 by Joshua Evans
        email                : joshuaevanslowell@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Joshua Evans'
__date__ = '2020-10-6'
__copyright__ = '(C) 2020 by Joshua Evans'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import (
                       QgsFeatureSink,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsProcessingParameterFile,
                       )

from .qscout_pin_algorithm import *

class PinDropperAlgorithm(QScoutPinAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    DROP_DATALESS_POINTS_INPUT = 'DROP_DATALESS_POINTS_INPUT'
    DATA_SOURCE_INPUT = 'FIELD_NAME_INPUT'
    DATA_SOURCE_FIELDS_TO_USE = 'DATA_SOURCE_FIELDS_TO_USE'
    PANEL_SIZE_INPUT = 'PANEL_SIZE_INPUT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):
        super().initAlgorithm(config)

        # fields to use
        param = QgsProcessingParameterString(
            self.DATA_SOURCE_FIELDS_TO_USE,
            self.tr("Fields to Use"),
            optional=True
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # panel size
        param = QgsProcessingParameterNumber(
            self.PANEL_SIZE_INPUT,
            self.tr("Panel Size"),
            minValue=0,
            defaultValue=0
        )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # drop data-less points
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.DROP_DATALESS_POINTS_INPUT,
                self.tr("Drop Data-less Points"),
                defaultValue=False  # should maybe change to false in production version
            )
        )

        # input data
        self.addParameter(
            QgsProcessingParameterFile(
                self.DATA_SOURCE_INPUT,
                self.tr("Input Data"),
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        self.preProcessAlgorithm(parameters, context)

        self.locatePoints(feedback)

        # 'relativize' the coordinates, so x and y both start at 1
        # this also includes orienting the coordinates according to the user's preferance
        self.relativize_coords()

        # load input data
        data, attrs = self.load_input_data(parameters, context)

        # set up fields for output layer
        out_fields = QgsFields()
        for n, dt in attrs:
            out_fields.append(QgsField(name=n, type=dt))

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        (self.sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields=out_fields,
            geometryType=QgsWkbTypes.Point,
            crs=self.bound_box_layer.crs(),
            sinkFlags=QgsFeatureSink.RegeneratePrimaryKey)

        # read values from source csv file
        # (for now generate random values from 1 to 5)

        # set output field values
        count = 0
        already_dropped = []
        not_dropped = []
        # first loop. add points from input data
        if data is not None:
            for entry in data:
                coords = (entry[self.input_col_attr_name], entry[self.input_row_attr_name])
                if coords in self._defined_points:
                    pin = self[coords]
                    # do conversions. qgis uses gdal, which is *VERY* finicky about fata types. gotta make sure
                    # data types are Python types, not numpy types.
                    vals = [DTYPE_CONVERSIONS[data.dtype[i].kind][1](entry[i]) for i in range(len(data.dtype))]
                    # add pin
                    count = self.add_pin_to_output(pin, vals, count)
                    # flag as dropped
                    already_dropped.append(coords)
                else:
                    # flag point as not in dropped points
                    not_dropped.append(coords)

        # second loop. add points not in input data
        if self.drop_dataless_points or data is None:
            for coords in self._defined_points:
                if coords not in already_dropped:  # don't re-add points from last loop
                    entry = [np.nan for _ in attrs]
                    # set col and row values
                    entry[self.col_attr_idx] = int(coords[0])
                    entry[self.row_attr_idx] = int(coords[1])
                    count = self.add_pin_to_output(self[coords], entry, count)

        for d in not_dropped:  # output non-dropped data in input data
            feedback.pushInfo("Did not drop coordinates for %d, %d." % d)

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}

    def load_input_data(self, parameters, context):
        """
        loads and processes input data from a .csv file provided
        assigns class attributes input_col_attr_name, col_attr_idx, input_row_attr_name, row_attr_idx
        """
        self.data_source = self.parameterAsFile(parameters, self.DATA_SOURCE_INPUT, context)
        self.drop_dataless_points = self.parameterAsBool(parameters, self.DROP_DATALESS_POINTS_INPUT, context)
        self.drop_dataless_points = self.drop_dataless_points or self.data_source is None
        fields_to_use = self.parameterAsString(parameters, self.DATA_SOURCE_FIELDS_TO_USE, context)

        attrs = []
        # set up fields to use
        fields_to_use_list = []
        if fields_to_use.strip():
            fields_to_use_list = list(map(lambda x: x.strip(), fields_to_use.rsplit(',')))

        if self.data_source.strip():  # empty strings are "falsey" so if there is text, this will be true
            # may raise exceptions. may have to improve descriptiveness of errors
            input_data = np.genfromtxt(self.data_source, delimiter=',', names=True, dtype=None)

            # read input data analysis parameters
            panel_size = self.parameterAsInt(parameters, self.PANEL_SIZE_INPUT, context)

            # assemble attrs array from hell
            # 'array' is a list of tuples of name, dtype and is filtered through fields_to_use
            attrs = [(input_data.dtype.names[i], input_data.dtype[i])
                             for i in range(len(input_data.dtype))
                             if ((not fields_to_use.strip()) or input_data.dtype.names[i] in fields_to_use_list)]
            # have to set up panel size here
            if panel_size > 0:
                # dtype not a huge deal here because it'll get set again a few lines down
                attrs = attrs + [(COL_NAME, np.dtype(np.int16))]
                self.input_col_attr_name = COL_NAME
                self.col_attr_idx = len(attrs) - 1
            else:
                # look for column or number
                col_regex = "([_\-\w]?[Cc]ol.?)|(.?[Nn]umber.?)"  # TODO: improve regex
                self.input_col_attr_name, self.col_attr_idx = match_index(input_data.dtype.names, col_regex)
                assert self.col_attr_idx > -1, "No column in the attached file can ve identified as 'column' or " \
                                               "'number'. Tip: if your data has a column for panels, you need to " \
                                               "specify the panel size."


            row_regex = "[_\-\w]?[Rr]ow"  # TODO: improve regex
            self.input_row_attr_name, self.row_attr_idx = match_index(input_data.dtype.names, row_regex)
            assert self.row_attr_idx > -1, "No column in the attached file can be identified as 'row'"

            # make array for processed data
            data = np.full(shape=input_data.shape, dtype=np.dtype(attrs), fill_value=np.nan)

            # grab grid dimensions
            x_mins, x_maxs, y_mins, y_maxs = self.calc_grid_dimensions()

            if panel_size > 0:
                # grab panel stuff
                panel_regex = ".?[Pp]anel.?"
                panel_attr_name, panel_attr_idx = match_index(input_data.dtype.names, panel_regex)
                assert panel_attr_idx > -1, "No column in the attached file can ve identified as 'panel'"
                # grab vine/plant stuff
                vine_regex = ".?([Vv]ine)|([Pp]lant).?"
                vine_attr_name, vine_attr_idx = match_index(input_data.dtype.names, vine_regex)
                assert vine_attr_idx > -1, "No column in the attached file can ve identified as 'vine' or 'plant"
                # process panel/plant data
                # TODO: implement negative value processing like for row and col inputs?
                data[self.input_col_attr_name] = panel_size * input_data[panel_attr_name] + input_data[vine_attr_name]
            else:
                negative_cols = input_data[self.input_col_attr_name] < 0
                # select x input data with negative values and process
                x_data_neg = x_maxs[input_data[self.input_row_attr_name][negative_cols].astype(np.int_)] +\
                             input_data[self.input_col_attr_name][negative_cols]
                # put processed x negative input data in data array
                data[self.input_col_attr_name][negative_cols] = x_data_neg
                # put normal input data in data array
                data[self.input_col_attr_name][negative_cols == False] = input_data[self.input_col_attr_name][negative_cols == False]

            # deal with row data, which is easier
            y_max = np.amax(y_maxs)
            negative_rows = input_data[self.input_row_attr_name] < 0
            data[self.input_row_attr_name][negative_rows] = y_max + input_data[self.input_row_attr_name][negative_rows]
            data[self.input_row_attr_name][negative_rows == False] = input_data[self.input_row_attr_name][negative_rows == False]

            # better way to do this than for-loop? IDK. using the _idx values breaks if not using all fields
            for i in range(len(attrs)):
                name, dt = attrs[i]
                if name == self.input_row_attr_name or name == self.input_col_attr_name:
                    attrs[i] = (name, np.dtype(np.int_))
                    # assign indexes so they can be right when they're used to assign values in processAlgorithm
                    if name == self.input_col_attr_name:
                        self.col_attr_idx = i
                    else:
                        self.row_attr_idx = i

            # put the rest of the input data in the processed data array
            for dt_name, _ in attrs:
                if dt_name == self.input_col_attr_name or dt_name == self.input_col_attr_name:
                    continue
                data[dt_name] = input_data[dt_name]

        else:  # if no input data was provided
            data = None
            if fields_to_use.strip():
                attrs = [(COL_NAME, np.dtype(np.int16)), (ROW_NAME, np.dtype(np.int16))]
                # use user-specified fields
                attrs.extend([(name, np.dtype(np.str)) for name in fields_to_use_list])  # sure, string dtype
            else:
                # if all else fails just call it "data" and move on
                attrs = [(COL_NAME, np.dtype(np.int16)), (ROW_NAME, np.dtype(np.int16)), ('data', np.dtype(np.str))]
            # set params
            self.input_col_attr_name = COL_NAME
            self.col_attr_idx = 0
            self.input_row_attr_name = ROW_NAME
            self.row_attr_idx = 1

        # do final run at processing attrs, so it reflects python data types.
        # TODO: should this line be moved to processAlgorithm?
        out_attrs_types = [(name, DTYPE_CONVERSIONS[t.kind][0]) for name, t in attrs]

        return data, out_attrs_types

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
        self.sink.addFeature(feat)
        return count + 1

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'droppins'

    def displayName(self):
        return self.tr("Drop Pins")

    def createInstance(self):
        return PinDropperAlgorithm()


