import weakref
from warnings import warn
from defcon.objects.base import BaseObject


class Component(BaseObject):

    """
    This object represents a reference to another glyph.

    **This object posts the following notifications:**

    ===============================
    Name
    ===============================
    Component.Changed
    Component.BaseGlyphChanged
    Component.TransformationChanged
    Component.IdentifierChanged
    ===============================
    """

    changeNotificationName = "Component.Changed"
    representationFactories = {}

    def __init__(self):
        super(Component, self).__init__()
        self._dirty = False
        self._baseGlyph = None
        self._transformation = (1, 0, 0, 1, 0, 0)
        self._identifier = None

    # ----------
    # Attributes
    # ----------

    # parents

    def _get_font(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.font

    font = property(_get_font, doc="The :class:`Font` that this component belongs to.")

    def _get_layerSet(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.layerSet

    layerSet = property(_get_layerSet, doc="The :class:`LayerSet` that this component belongs to.")

    def _get_layer(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.layer

    layer = property(_get_layer, doc="The :class:`Layer` that this component belongs to.")

    def _get_glyph(self):
        return self.getParent()

    glyph = property(_get_glyph, doc="The :class:`Glyph` that this component belongs to.")

    def _get_bounds(self):
        from robofab.pens.boundsPen import BoundsPen
        glyph = self.getParent()
        if glyph is None:
            return None
        font = glyph.getParent()
        if font is None:
            return None
        pen = BoundsPen(font)
        self.draw(pen)
        return pen.bounds

    bounds = property(_get_bounds, doc="The bounds of the components's outline expressed as a tuple of form (xMin, yMin, xMax, yMax).")

    def _get_controlPointBounds(self):
        from fontTools.pens.boundsPen import ControlBoundsPen
        glyph = self.getParent()
        if glyph is None:
            return None
        font = glyph.getParent()
        if font is None:
            return None
        pen = ControlBoundsPen(font)
        self.draw(pen)
        return pen.bounds

    controlPointBounds = property(_get_controlPointBounds, doc="The control bounds of all points in the components. This only measures the point positions, it does not measure curves. So, curves without points at the extrema will not be properly measured.")

    def _set_baseGlyph(self, value):
        oldValue = self._baseGlyph
        if value == oldValue:
            return
        self._baseGlyph = value
        self.postNotification(notification="Component.BaseGlyphChanged", data=dict(oldValue=oldValue, newValue=value))
        self.dirty = True

    def _get_baseGlyph(self):
        return self._baseGlyph

    baseGlyph = property(_get_baseGlyph, _set_baseGlyph, doc="The glyph that the components references. Setting this will post *Component.BaseGlyphChanged* and *Component.Changed* notifications.")

    def _set_transformation(self, value):
        oldValue = self._transformation
        if value == oldValue:
            return
        self._transformation = value
        self.postNotification(notification="Component.TransformationChanged", data=dict(oldValue=oldValue, newValue=value))
        self.dirty = True

    def _get_transformation(self):
        return self._transformation

    transformation = property(_get_transformation, _set_transformation, doc="The transformation matrix for the component. Setting this will post *Component.TransformationChanged* and *Component.Changed* notifications.")

    # -----------
    # Pen Methods
    # -----------

    def draw(self, pen):
        """
        Draw the component with **pen**.
        """
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """
        Draw the component with **pointPen**.
        """
        try:
            pointPen.addComponent(self._baseGlyph, self._transformation, identifier=self.identifier)
        except TypeError:
            pointPen.addComponent(self._baseGlyph, self._transformation)
            warn("The addComponent method needs an identifier kwarg. The component's identifier value has been discarded.", DeprecationWarning)

    # -------
    # Methods
    # -------

    def move(self, (x, y)):
        """
        Move the component by **(x, y)**.

        This posts *Component.TransformationChanged* and *Component.Changed* notifications.
        """
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = self._transformation
        xOffset += x
        yOffset += y
        self.transformation = (xScale, xyScale, yxScale, yScale, xOffset, yOffset)

    def pointInside(self, (x, y), evenOdd=False):
        """
        Returns a boolean indicating if **(x, y)** is in the
        "black" area of the component.
        """
        from fontTools.pens.pointInsidePen import PointInsidePen
        glyph = self.getParent()
        if glyph is None:
            return False
        font = self.getParent()
        if font is None:
            return False
        pen = PointInsidePen(glyphSet=font, testPoint=(x, y), evenOdd=evenOdd)
        self.draw(pen)
        return pen.getResult()

    # ----------
    # Identifier
    # ----------

    def _get_identifiers(self):
        identifiers = None
        parent = self.getParent()
        if parent is not None:
            identifiers = parent.identifiers
        if identifiers is None:
            identifiers = set()
        return identifiers

    identifiers = property(_get_identifiers, doc="Set of identifiers for the glyph that this component belongs to. This is primarily for internal use.")

    def _get_identifier(self):
        return self._identifier

    def _set_identifier(self, value):
        oldIdentifier = self.identifier
        if value == oldIdentifier:
            return
        # don't allow a duplicate
        identifiers = self.identifiers
        assert value not in identifiers
        # free the old identifier
        if oldIdentifier in identifiers:
            identifiers.remove(oldIdentifier)
        # store
        self._identifier = value
        if value is not None:
            identifiers.add(value)
        # post notifications
        self.postNotification("Component.IdentifierChanged", data=dict(oldValue=oldIdentifier, newValue=value))
        self.dirty = True

    identifier = property(_get_identifier, _set_identifier, doc="The identifier. Setting this will post *Component.IdentifierChanged* and *Component.Changed* notifications.")

    def generateIdentifier(self):
        """
        Create a new, unique identifier for and assign it to the contour.
        This will post *Component.IdentifierChanged* and *Component.Changed* notifications.
        """
        identifier = makeRandomIdentifier(existing=self.identifiers)
        self.identifier = identifier


def _testIdentifier():
    """
    >>> from defcon import Glyph
    >>> glyph = Glyph()
    >>> component = Component()
    >>> glyph.appendComponent(component)
    >>> component.identifier = "component 1"
    >>> component.identifier
    'component 1'
    >>> list(sorted(glyph.identifiers))
    ['component 1']
    >>> component = Component()
    >>> glyph.appendComponent(component)
    >>> component.identifier = "component 1"
    Traceback (most recent call last):
        ...
    AssertionError
    >>> component.identifier = "component 2"
    >>> list(sorted(glyph.identifiers))
    ['component 1', 'component 2']
    >>> component.identifier = "not component 2 anymore"
    >>> component.identifier
    'not component 2 anymore'
    >>> list(sorted(glyph.identifiers))
    ['component 1', 'not component 2 anymore']
    >>> component.identifier = None
    >>> component.identifier
    >>> list(sorted(glyph.identifiers))
    ['component 1']
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
