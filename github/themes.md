# Themes

To make your own theme, create a `.css` file and at the beginning of the file create a comment in which you specify information about the theme in json format.

Example:
```css
/*
{
    "_": "Theme",
    "version": "1.0",
    "name": "My Theme name",
    "author": "My nick name",
    "image": ""
}
*/

body{
    ...
}
```

### Metadata

|            |             |                                      |             |
|------------|-------------|--------------------------------------|-------------|
| _          | "Theme"     | Theme Declaration                    |             |
| version    | "1.0"       | Theme version                        |             |
| **name**   | `string`    | Theme name                           | _required_  |
| **author** | `string`    | Theme author                         | _preferred_ |
| **image**  | `string`    | Theme icon (`data:image` or `https`) | _required_  |

You can see examples of ready-made themes [here](themes/).

### Local themes

To test your theme locally, create a `themes` folder next to the `.exe` file<br>
(or click the `More` button in the Settings themes section and the folder will be automatically created)<br>
and place your `.css` file in this folder.

### Web themes

Then you can upload your theme to this repository and after moderation check, your theme can get into the program.
