
"""
Need to add the hook python file in the config.env.includes.settings.tk-multi-publish2.yml
"""


import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

from tank_vendor import six

# Inherit from mayaPublishBase.py 
# Check config.env.includes.settings.tk-multi-publish2.yml
HookBaseClass = sgtk.get_hook_baseclass()

class MayaAssetScenePublishPlugin(HookBaseClass):

    def accept(self, settings, item):

        self.logger.info("Asset Scene Publish | accept")

        accepted = True
        # Get the publish plugin publish template.
        # This template is assgin in config.env.includes.settings.tk-multi-publish2.yml
        template_name = settings[self.publishTemplate].value
        # Check if the template is valid.
        accepted, publish_template = self.checkPublishTemplate(template_name)
        # we've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties[self.propertiesPublishTemplate] = publish_template
        # because a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        item.context_change_allowed = False

        return {"accepted": accepted, "checked": True}

    def validate(self, settings, item):

        self.logger.info("Asset Scene Publish | validate")

        # We use the MayaAsset class stored in the item to check if the current asset is a valid asset.
        mayaAsset = item.properties.get("assetObject")

        # Check if the asset root is a valid asset.
        if not (mayaAsset.isValid()):
            error_msg = "The asset %s is not a valid. Please check the asset group structure."
            self.logger.error(error_msg, extra=_get_save_as_action)
            raise Exception(error_msg)

        # Add the publish path datas to the publish item.
        # That allow us to reuse the datas for the publish.
        self.addPublishDatasToPublishItem(item, self.propertiesPublishTemplate)

        # run the base class validation
        return super(MayaAssetScenePublishPlugin, self).validate(settings, item)


    def publish(self, settings, item):

        self.logger.info("Asset Publish | publish")

        publisher = self.parent

        # Get the item asset object.
        mayaObject = item.properties["assetObject"]

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        # Select the asset before save.
        cmds.select(clear=True)
        cmds.select(mayaObject.name)

        # Save the asset.
        cmds.file(publish_path, force=True, type="mayaAscii", exportSelected=True)

        # let the base class register the publish
        super(MayaAssetScenePublishPlugin, self).publish(settings, item)


    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        pass

    @property
    def publishTemplate(self):
        return "Publish Template"

    @property
    def propertiesPublishTemplate(self):
        return "asset_scene_publish_template"

    @property
    def description(self):
        return """
        <p>This plugin publish the selected assets for the model pipeline step
        You need to select root transform of the asset.</p>
        """

    @property
    def settings(self):
        # inherit the settings from the base publish plugin
        base_settings = super(MayaAssetScenePublishPlugin, self).settings or {}

        # settings specific to this class
        maya_publish_settings = {
            self.publishTemplate : {
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