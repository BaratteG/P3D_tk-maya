
import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()

class MayaAssetAlembicMIPublishPlugin(HookBaseClass):

    def accept(self, settings, item):

        accepted        = True
        publisher       = self.parent
        template_name   = settings["Asset Alembic MI Publish Template"].value

        # We use the MayaAsset Class stored in the item to do checking.
        mayaAsset = item.properties.get("assetObject")

        # Check if the group MI is not empty.
        # If its empty we don't need to publish it.
        meshesMI = mayaAsset.meshesMI
        if(len(meshesMI) == 0):
            self.logger.debug("The Mi group is empty.")
            accepted= False

        # ensure the publish template is defined and valid and that we also have
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            self.logger.debug(
                "The valid publish template could not be determined for the "
                "session geometry item. Not accepting the item."
            )
            accepted = False

        # we've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties["publish_template"] = publish_template

        # because a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        item.context_change_allowed = False

        return {"accepted": accepted, "checked": True}

    def validate(self, settings, item):

        path = _session_path()

        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Maya session has not been saved."
            self.logger.error(error_msg, extra=_get_save_as_action())
            raise Exception(error_msg)
        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)
        self.logger.info("Path : %s" % path)

        # get the configured work file template
        work_template = item.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        self.logger.info("Work Template : %s" % work_template)
        self.logger.info("Publish Template : %s" % publish_template)

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)
        work_fields["lod"] = "mi"

        self.logger.info("Work Fields : %s" % work_fields)
        # ensure the fields work for the publish template
        missing_keys = work_template.missing_keys(work_fields)
        if missing_keys:
            error_msg = (
                "Work file '%s' missing keys required for the "
                "publish template: %s" % (path, missing_keys)
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.
        item.properties["path"] = publish_template.apply_fields(work_fields)
        item.properties["publish_path"] = item.properties["path"]

        self.logger.info("Path Properties : %s" % item.properties.get("path"))
        self.logger.info("Publish Path Properties : %s" % item.properties.get("publish_path"))

        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(MayaAssetAlembicMIPublishPlugin, self).validate(settings, item)


    def publish(self, settings, item):
        pass


    @property
    def description(self):
        return """
        <p>This plugin publish the selected assets for the model pipeline step
        You need to select root transform of the asset.</p>
        """

    @property
    def settings(self):
        # inherit the settings from the base publish plugin
        base_settings = super(MayaAssetAlembicMIPublishPlugin, self).settings or {}

        # settings specific to this class
        maya_publish_settings = {
            "Asset Alembic MI Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }      
        }

        # update the base settings
        base_settings.update(maya_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        return ["maya.asset"]

def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if path is not None:
        path = six.ensure_str(path)

    return path


def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

    # default save callback
    callback = cmds.SaveScene

    # if workfiles2 is configured, use that for file save
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": callback,
        }
    }