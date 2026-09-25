#!/bin/bash

install_dir="/var/www/$app"
data_dir="/var/lib/$app"
port="$(ynh_find_port --port=8000)"
