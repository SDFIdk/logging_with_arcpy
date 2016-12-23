# logging_with_arcpy

A helpful tool when using the Python `logging` module together with `arcpy` from Esri.

It primarily addresses two issues:

* makes logging work for tools executed from within ArcMap (otherwise
  there are some initialisation issues, because the logging session
  doesn't get restarted for multiple tool runs in the same ArcMap
  session).
* allows logging to add a handler that prints output to the ArcMap
  output dialog (this part largely adopted from
  http://gis.stackexchange.com/questions/135920/arcpy-logging-error-messages).

See logging_with_arcpy.html for details.
