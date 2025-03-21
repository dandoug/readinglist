# Sources for libs

## Including libs from these directories

In templates, use something like
```html
<link href="{{ url_for('static', filename='css/bootstrap-treeview.min.css') }}" rel="stylesheet"/>
```
or
```html
<script src="{{ url_for('static', filename='js/bootstrap-treeview.min.js') }}"></script>
```
for files located in the [css](css) or [js](js) directories, as appropriate.

## Sources for libs imported via CDN

### PatternFly Treeview
* [patternfly/patternfly-bootstrap-treeview](https://github.com/patternfly/patternfly-bootstrap-treeview/tree/master) - includes hierarchical check functions

### Bootstrap 4
* [Bootstrap 4.6](https://getbootstrap.com/docs/4.6/getting-started/introduction/) - to be compatible with PatternFly Treeview

### Bootswatch
* [Sandstone](https://bootswatch.com/4/sandstone/) - override default Bootstrap4 styling... other choices available at Bootswatch.  Sandstone installed as [bootstrap.min.css](css/bootstrap.min.css).

### JQuery
* [JQuery 3.7](https://api.jquery.com/)

### Font Awesome

* [Font Awesome 4.7](https://fontawesome.com/v4/icons/) - includes hollow box and hollow box with check and minus
