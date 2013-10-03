﻿// String.startsWithif (typeof String.prototype.startsWith != 'function') {  String.prototype.startsWith = function (str){    return this.slice(0, str.length) == str;  };}function fileExists(path) {    var file = new File(path);    return file.exists;}function isSubstring(str1, str2) {    return str2.indexOf(str1) != -1;}var inputs = { "shared_path": "shared path", "base_url": "base url", "username":"username", "password":"password", "block_size": "block size" }var w = new Window("palette","Submit Render");var group = w.add("group {alignChildren: 'fill', orientation: 'column'}");var fields = {};var groups = {};for(key in inputs) {        groups[key] = group.add("group")        label = groups[key].add("statictext", undefined, inputs[key]);        label.size = [120,15];        fields[key] = groups[key].add("edittext",undefined,undefined);        fields[key].characters=50;}fields["shared_path"].characters = 45;btn = groups["shared_path"].add("button {text:'...'}");btn.onClick = pick_shared_path;btn.size = [30,15];// render_queue optionscomps = []num = app.project.renderQueue.numItemsfor(var i = 1; i <= num; i++) {    comps[i-1] = app.project.renderQueue.item(i).comp.name;}groups["render_queue_item"] = group.add("group")label = groups["render_queue_item"].add("statictext",[0,0,200,15],"render_queue item")label.size = [120,15]fields["render_queue_item"] = groups["render_queue_item"].add("dropdownlist", undefined,comps)fields["render_queue_item"].minimumSize.width = 360;fields["render_queue_item"].selection = fields["render_queue_item"].items[0];phg = w.add("group");fields["posthook"] = phg.add("checkbox {text:'transcode result'}");phg.add("statictext",undefined,"fps");fields["fps"] = phg.add("edittext",undefined,undefined);options = ["h264","prores","dnxhd","proxy"];for(var i = 0; i < options.length; i++) {    fields[options[i]] = phg.add("checkbox {text:'"+options[i]+"'}");}var config = read_config();populate_inputs(config);submitButton = w.add("button {text:'save and submit'}");submitButton.onClick = submit;w.show();function write_config() {    var mandatory = ["shared_path","base_url","username","password","render_queue_item"],          config = {},          error = "";    for(label in fields) {        if(fields[label] instanceof EditText) {            if(label in mandatory && fields[label].text == "") {                error = label;            }            config[label] = fields[label].text;        }        else if(fields[label] instanceof Checkbox) {            config[label] = fields[label].value;        }        else if(fields[label] instanceof DropDownList) {            if(fields[label].selection == null) {                error = label;            }            config[label] = fields[label].selection;        }    }    if(error != "") {        alert(error + " is not set");        return false;    }    cfg_string = stringify(config);    writeToFile("/Users/shared/Adobe/ae_submitter_config.txt",cfg_string);    return config;}function writeToFile(filepath, content) {    f = new File(filepath);    f.open("w");    f.write(content);    f.close();}function populate_inputs(config) {    for(prop in config) {        if(fields[prop] instanceof EditText) {            fields[prop].text = config[prop];        }        else if(fields[prop] instanceof Checkbox) {            fields[prop].value = config[prop];        }    }}function read_config() {    f = new File("/Users/shared/Adobe/ae_submitter_config.txt");    if(f.open("r")) {        content = f.read();        eval("config = " + content + ";");    }    return config;}function checkSaved() {    return app.project.file !== null;}function stringify(config) {    cfg_string = "{";    for( prop in config ) {        if(fields[prop] instanceof EditText) {                  cfg_string += "\"" + prop + "\":\"" + config[prop] + "\",";        }        else if(fields[prop] instanceof DropDownList) {            cfg_string += "\"" + prop + "\":\"" + config[prop].toString() + "\",";        }                else if(fields[prop] instanceof Checkbox) {            cfg_string += "\"" + prop + "\":" + config[prop] + ",";        }        else {            cfg_string += "\"" + prop + "\":\"" + config[prop] + "\",";        }          }    cfg_string = cfg_string.substring(0,cfg_string.length -1)    cfg_string += "}";    return cfg_string;}function submit() {    config = write_config();    if(!config) {        return;    }    var render_queue_index = config["render_queue_item"].index+1;    config["render_queue_index"] = render_queue_index;    cfg_string = stringify(config);       if(!checkSaved()) {        alert("Project must be saved first");        return;    }    // get render_queue item    var rqi = app.project.renderQueue.item(render_queue_index);    var fps = 1/rqi.comp.frameDuration;    var frame_start = rqi.timeSpanStart * fps;    var frame_end = (rqi.timeSpanStart + rqi.timeSpanDuration) * fps - 1;    config["frame_start"] = frame_start;    config["frame_end"] = frame_end;        src_path = app.project.file.fsName    if(!src_path.startsWith(config["shared_path"])) {        alert("Project is not saved on shared path");        return;    }    var ext_split = src_path.split('.');    var ext = ext_split.pop();    var name = ext_split.pop();    var dir_split = name.split("/");    var basename = dir_split.pop();    var dirname = "";    for(var i = 0; i < dir_split.length; i++) {        dirname += dir_split[i] + "/";    }    submit_path = dirname + "_" + basename + "_submit." + ext;        if(fileExists(submit_path)) {        if(!Window.confirm("File was already submitted, submit again? (overwrites submitted file)",true,"Confirm")) {            return;        }    };        for(var i = 1; i <= rqi.numOutputModules; i++) {        var file = rqi.outputModule(i).file        if(file == "" || !file) {            alert("At least one output module has no output file");            return;        }    }    curfolder = (new File($.fileName)).parent.absoluteURI;    params = "'"+ cfg_string + "'" + " 'aftereffectsproject' '" + src_path + "' " + frame_start + " " + frame_end;    alert(system.callSystem("python /Users/shared/Adobe/submit_to_dire.py " + params));        }function pick_shared_path() {    path = Folder.selectDialog("Select path").fsName;    fields["shared_path"].text = path;}