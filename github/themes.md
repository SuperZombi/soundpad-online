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

