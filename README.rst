==============================
Configuration Console (ConCon)
==============================


.. image:: https://img.shields.io/pypi/v/concon.svg
        :target: https://pypi.python.org/pypi/concon

.. image:: https://img.shields.io/travis/JNev/concon.svg
        :target: https://travis-ci.org/calcite/concon

.. image:: https://readthedocs.org/projects/concon/badge/?version=latest
        :target: https://concon.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/calcite/concon/shield.svg
     :target: https://pyup.io/repos/github/calcite/concon/
     :alt: Updates


Configuration tool for defices supporting the "Uniprot" protocol over USB (HID profile).
This tool doesn't need any device-specific driver of ini file, everything is read from
the device.

Compatible devices
------------------

Devices must fulfill following to communicate with ConCon:

* USB interface with "uniprot" communication layer (data secure)
* Device must support the ``generic driver`` (common way how to communicate
    with any low level driver) and ``HW bridge uniprot`` (data from
    generic driver are send through uniprot)

Installation
------------

The easiest way to install ConCon is with pip (pip3)::

    $ sudo pip install git+https://github.com/calcite/concon.git

Workflow
--------

The command-line tool is usually used in the following workflow:

#. Download all device options and dynamically create configuration file::

    $ concon read config-file.cfg


#. User modify configuration file
#. Upload configuration back to device::

    $ concon write config-file.cfg

In case of several connected devices
++++++++++++++++++++++++++++++++++++

If more then one Uniprot device is connected to the same PC, the device ID
needs to be specified as command-line parameter.

Get list of devices::

    $ concon list
      More than one configurable devices detected.
      Choose one from below and run again with -d [0 ~ 1] option.
       Dev# 0 <Sonochan mkII #00>
       Dev# 1 <Sonochan mkII #01>

Using one particular device::

    $ concon -d 0 read config-file.cfg


Protocol/Description field syntax detail:
-----------------------------------------

Currently the system only generates config files with "windows" ini-like syntax,
(with description fields in comments), but it's planned to support GUI
in the future (most likely in property-grid-like fashion). For that, some
special syntax can be used to define GUI of each setting.

List of option
++++++++++++++

``{L} val1:option1; val2:option2; val3:option3;...;N:some final note``

Final note is optional.

Checkbox
++++++++

``{C} option_description``

Slider
++++++

``{S} option_description; step:value``

Arrowbox
++++++++

``{A} option_description; step:value``

Eval expansion
++++++++++++++

This option is to save the length of strings which needs to be stored in the
MCU's code for descriptors. Instead, one can write a Python
expression which will be expanded to a string and processed.

Example::

    {L}0:fsref/1; 1:fsref/1.5; 2:fsref/2; 3:fsref/2.5; 4:fsref/3;
    5:fsref/3.5; 6:fsref/4; 7:fsref/4.5; 8:fsref/5; 9:fsref/5.5; 10:fsref/6


This is may be way too long for MCU with limited code memory. Easier to use
eval expansion (start line with '=')::

    ='{L}'+'; '.join(['{0}:fsref/{1}'.format(i,i*0.5+1) for i in range(0,11)])

which will be expanded to the same thing.

* Free software: MIT license
* Documentation: https://concon.readthedocs.io.


Notes
-----
* Tested on Linux with Python 2.7, 3.2, 3.3 and 3.4
* If you have **problems with permissions**, you can always use ``sudo``, but
  better way is create rule for udev. Create file 
  `/etc/udev/rules.d/11-alps_devices.rules`
  and paste there following line:
  ``SUBSYSTEM=="usb", MODE="0644", GROUP="plugdev"``.
  Unplug USB device, restart udev, plug USB device and try again. Also make
  sure you are at group ``plugdev``
* Tested on Windows XP and Windows 7 with Python 2.7 (but it should work on
   version 3.2, 3.3 and so on)
* For more info run application with "-h" parameter

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

