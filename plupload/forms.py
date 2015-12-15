# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms import Form
from django.forms.fields import FilePathField
from django.forms.utils import flatatt
from django.forms.widgets import Input
from django.template.loader import render_to_string
from django.template.defaultfilters import capfirst
from plupload.settings import (UPLOAD_TO, EXTENSIONS, MAX_FILE_SIZE, UNIQUE_NAMES, UPLOAD_CHMOD,
                               SHOW_REMOVE, SHOW_THUMBNAIL, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, RESIZE_WIDTH,
                               RESIZE_HEIGHT, RESIZE_QUALITY, AUTO_START, STATIC_URL, CHUNK_SIZE)
import os


def convert_bytes(bytes):
    """
    Converts number of bytes into a string suitable for plupload max_file_size parameter:
    max_file_size
    Maximum file size that the user can pick. This string can be in the following formats 100b, 10kb, 10mb, 1gb.
    """
    bytes = float(bytes)
    if bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.0fgb' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.0fmb' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.0fkb' % kilobytes
    else:
        size = '%.0fb' % bytes
    return str(size)


class PluploadInputWidget(Input):
    """
    Renders an input tag (hidden) and the plupload window connected to it
    """
    input_type = 'text'

    def __init__(self, attrs=None):
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}

    def render(self, name, value, attrs=None):
        from plupload.models import PluploadControlCode
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        final_attrs['class'] = '%s pluploader' % final_attrs['class'] if final_attrs.get('class') else 'pluploader'
        id = final_attrs.get('id', '')
        self.upload_to = final_attrs.pop('upload_to', UPLOAD_TO).rstrip('/')  # UPLOAD_TO relative to MEDIA_ROOT
        self.resize_width = final_attrs.pop('resize_width', RESIZE_WIDTH)
        self.resize_height = final_attrs.pop('resize_height', RESIZE_HEIGHT)
        self.resize_quality = final_attrs.pop('resize_quality', RESIZE_QUALITY)
        self.extensions = final_attrs.pop('extensions', EXTENSIONS)  # allowed extensions for this field
        self.max_file_size = final_attrs.pop('max_file_size', MAX_FILE_SIZE)  # max allowed file size in Mb
        self.unique_names = final_attrs.pop('unique_names', UNIQUE_NAMES)  # change uploaded file name to make it unique
        self.upload_chmod = final_attrs.pop('upload_chmod', UPLOAD_CHMOD)  # attempt chmod once file is uploaded
        self.show_remove = final_attrs.pop('show_remove', SHOW_REMOVE)  # shows 'remove' checkbox
        self.show_thumbnail = final_attrs.pop('show_thumbnail', SHOW_THUMBNAIL)  # shows as thumbnail of uploaded image
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))  # upload_to + filename
        self.uploaded_filename = ''
        self.uploaded_url = os.path.join(settings.MEDIA_URL, final_attrs['value']) if final_attrs.get('value') else ''
        thumbnail_style = ''  # width/height of the uploaded image thumbnail
        error = ''
        if final_attrs.get('value'):
            self.uploaded_filename = final_attrs['value'].replace(self.upload_to, '', 1).strip('/')
            if os.path.isfile(os.path.join(settings.MEDIA_ROOT, final_attrs['value'].lstrip('/'))):
                if self.show_thumbnail:
                    if THUMBNAIL_WIDTH or THUMBNAIL_HEIGHT:
                        thumbnail_style = ''
                        if THUMBNAIL_WIDTH:
                            thumbnail_style += 'width:%spx;' % THUMBNAIL_WIDTH
                        if THUMBNAIL_HEIGHT:
                            thumbnail_style += 'height:%spx;' % THUMBNAIL_HEIGHT
            else:
                error = u'Warning: file does not exist! It has probably been moved or deleted.'
        control_code = PluploadControlCode()
        control_code.upload_to = self.upload_to
        control_code.save()
        if self.extensions:
            self.extensions = [x.strip().lower() for x in self.extensions if x] + \
                              [x.strip().upper() for x in self.extensions if x] + \
                              [capfirst(x.strip().lower()) for x in self.extensions if x]
        html = render_to_string('plupload/widget.html', {
            'id': id,
            'final_attrs': flatatt(final_attrs),
            'upload_to': self.upload_to,
            'uploaded_url': self.uploaded_url,
            'uploaded_filename': self.uploaded_filename,
            'thumbnail_style': thumbnail_style,
            'error': error,
            'control_code': control_code.code,
            'auto_start': AUTO_START,
            'STATIC_URL': STATIC_URL,
            'chunk_size': CHUNK_SIZE,
            'resize_width': str(self.resize_width),  # to avoid 1024 becoming 1.024
            'resize_height': str(self.resize_height),
            'resize_quality': self.resize_quality,
            'extensions': self.extensions,
            # a string formatted for max_file_size setting, i.e. '2mb' '1000kb' '500000b', etc.:
            'max_file_size': convert_bytes(float(self.max_file_size)*1048576) if self.max_file_size else '',
            'unique_names': self.unique_names,
            'upload_chmod': self.upload_chmod,
            'show_remove': self.show_remove,
            'show_thumbnail': self.show_thumbnail,
        })
        return mark_safe(html)


class PluploadFormField(FilePathField):
    """
    A subclass of forms.FilePathField that renders a plupload window
    """
    widget = PluploadInputWidget

    def __init__(self, upload_to, match=None, recursive=False, allow_files=True, allow_folders=False, required=True,
                 widget=None, label=None, initial=None, help_text=None, resize_width=None, resize_height=None,
                 resize_quality=None, extensions=[], max_file_size=None, unique_names=False, upload_chmod=None,
                 show_remove=False, show_thumbnail=False, *args, **kwargs):
        self.match, self.recursive = match, recursive
        widget = widget or self.widget(attrs={'readonly': 'readonly'})
        if isinstance(widget, type):
            widget = widget()
        self.upload_to = upload_to  # FilePathField actually requires a 'path' attribute
        # custom, 'upload_to' is a path relative to settings.MEDIA_ROOT, like FileField 'upload_to',
        # while FilePathField's 'path' is an absolute path: we use the absolute path, since we are subclassing
        # FilePathField
        self.path = kwargs.pop('path', os.path.join(settings.MEDIA_ROOT, upload_to.rstrip('/')))
        # resize_to = None
        # if 'resize_to' in kwargs.keys():
            # resize_to = kwargs.pop('resize_to') or None
        widget.attrs['resize_width'] = ''
        widget.attrs['resize_height'] = ''
        widget.attrs['resize_quality'] = ''
        if resize_width:
            widget.attrs['resize_width'] = resize_width
        if resize_height:
            widget.attrs['resize_height'] = resize_height
        if resize_quality:
            widget.attrs['resize_quality'] = resize_quality
        widget.attrs['upload_to'] = upload_to
        widget.attrs['extensions'] = extensions  # allowed extensions for this field
        widget.attrs['max_file_size'] = max_file_size  # max allowed file size in Mb
        widget.attrs['unique_names'] = unique_names  # change uploaded file name to make it unique
        widget.attrs['upload_chmod'] = upload_chmod  # attempt chmod once file is uploaded
        widget.attrs['show_remove'] = show_remove  # shows 'remove' checkbox
        widget.attrs['show_thumbnail'] = show_thumbnail  # shows as thumbnail of the uploaded image
        super(FilePathField, self).__init__(choices=(), required=required, widget=widget, label=label, initial=initial,
                                            help_text=help_text, *args, **kwargs)

    def validate(self, value):
        """
        Validates that the input is in self.choices.
        """
        if value:
            if not self.valid_value(value) or value != '$remove$':
                if not self.check_file_is_uploaded(value):
                    raise ValidationError(self.error_messages['invalid_choice'] % {'value': value})

    def check_file_is_uploaded(self, file_rel_path):
        """
        Checks if file has really been transferred
        """
        # file_rel_path path relative to settings.MEDIA_ROOT
        if file_rel_path and os.path.isfile(os.path.join(settings.MEDIA_ROOT, file_rel_path)):
            return True
        return False


class PluploadForm(Form):
    file = PluploadFormField(upload_to=UPLOAD_TO,)
