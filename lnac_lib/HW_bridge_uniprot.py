#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
#
# @brief Bridge between universal protocol and hardware
#
# 
#
# @author Martin Stejskal
#

from uniprot import *



# @brief "Constants"
# @{
# options: debug, release
const_HW_BRIDGE_uniprot_VERSION = "debug"
##
# @}

##
# @brief Print message only if version is debug
def print_if_debug( string ):
    global const_HW_BRIDGE_uniprot_VERSION
    if const_HW_BRIDGE_uniprot_VERSION == "debug":
        print( string )



##
# @brief Connect to the target device if possible
def bridge_init():
    return Uniprot_init()

def bridge_close():
    return Uniprot_close()

def bridge_task():
    print("Bridge task")