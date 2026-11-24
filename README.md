# Zynthian-UI Widgets

A collection of independent, community-developed touchscreen UI widgets for Zynthian.

This repository currently contains **one widget**, **Ultramaster KR-106 UI v0.5.2**, for the **original KR-106 LV2 synthesizer** already available on Zynthian Tomita.

This repository does **not** contain synthesizer engines, audio DSP binaries or patches to Zynthian core.

## Widgets

| Widget | Host plugin | Version | Details |
|---|---|---|---|
| **Ultramaster KR-106 UI** | [`https://kayrock.org/kr106`](https://kayrock.org/kr106) | **0.5.2** | [Readme and installation](zynthian-UI%20widgets/Ultramaster%20KR-106%20UI/README.md) |

## Structure

```text
zynthian-widgets/                         (GitHub repository)
  README.md
  LICENSE
  zynthian-UI widgets/                   (UI-only collection)
    Ultramaster KR-106 UI/               (independent project)
      README.md
      CHANGELOG.md
      RELEASE_NOTES.md
      kr106_gui-zyngui.lv2/              (installable LV2 UI bundle)
        manifest.ttl
        zynthian_widget_kr106_gui.py
        zynthian_widget_kr106_gui.html
        ...
```

Additional **UI-only** projects can be added as siblings of `Ultramaster KR-106 UI/`.
Other kinds of work, if introduced in the future, may be organized in other folders (or separate repositories), independently of this UI collection.

The directory names used here deliberately match the requested public names, including spaces. Quote the paths when using Bash or package installation scripts. The internal LV2 bundle name and URIs must remain unchanged for Tomita compatibility.

## Releases and catalog

For this multi-widget repository, use **widget-specific tags** such as `ultramaster-kr106-ui-v0.5.2`, so future projects can have independent versions. A GitHub release is not an official Zynthian catalog entry.

Publishing in the Zynthian package catalog is a separate pull request to [zynthian/zynthian-packages](https://github.com/zynthian/zynthian-packages), with the appropriate `Widgets/` metadata and installation script. The installation script must use the correct subfolder of this repository.

## License

GPL-3.0. This is a community project, not an official Zynthian or Ultramaster KR-106 release.
