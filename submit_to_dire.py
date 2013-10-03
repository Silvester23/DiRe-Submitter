import os
import sys
import shutil
import json

if sys.version_info[0] >= 3:
    from urllib.parse import urlencode
    import urllib.request as urllib2
    import urllib.parse as urlparse
else:
    from urllib import urlencode
    import urllib2
    import urlparse

def submit_to_dire(args):
    config, project_type, src_path, frame_start, frame_end = args
    
    ret = ""
    
    def relative_path():
        relative_path = submit_path()[len(config['shared_path']):]
        while relative_path.startswith('/'):
            relative_path = relative_path[1:]
        return relative_path
    
    def submit_path():
        name, ext = os.path.splitext(src_path)
        dirname, basename = os.path.split(name)
        return os.path.join(dirname, '_' + basename + '_submit' + ext).replace(os.sep, '/')
        
    if __name__ == "__main__":
        def message(msg):
            print(msg)
            return ""
    else:
        def message(msg):
            return msg
    
    task_type = None
    
    if project_type not in ["mayaproject","nukescript","aftereffectsproject","blenderscene"]:
        ret = message("invalid project type")
        return ret
    
    login_url = urlparse.urljoin(config['base_url'], 'admin/')
    add_url = urlparse.urljoin(login_url, 'tasks/%s/add/' % (project_type))
    cookies = urllib2.HTTPCookieProcessor()
    urlopen = urllib2.build_opener(cookies)
    csrftoken = ''      

    try:
        page = urlopen.open(login_url)
    except urllib2.HTTPError as e:
        ret = message("HTTP Error code: " + str(e.code))
        return ret

    
    for cookie in cookies.cookiejar:
        if cookie.name == 'csrftoken':
            csrftoken = cookie.value
    params = urlencode([('csrfmiddlewaretoken', csrftoken),
                               ('username', config['username']),
                               ('password', config['password']),
                               ('this_is_the_login_form', '1'),
                               ('next', '/admin/')])
                               
    if sys.version_info[0] >= 3:
        params = params.encode("utf-8")
    
    page = urlopen.open(login_url, params)
    content = page.read()
    
    if sys.version_info[0] >= 3:
        content = content.decode("utf-8")
    
    if "Welcome," not in content:
        ret = message('Login unsuccessful')
        return ret
    
    #copy project file to submit_path
    shutil.copyfile(src_path,submit_path())
    
    post_hook = ''
    if config['posthook']:
        post_hook = '0'
    post_hook_options = {'fps': config['fps']}
    if config['proxy']:
        post_hook_options['proxy'] = True
    if config['h264']:
        post_hook_options['h264'] = True
    if config['prores']:
        post_hook_options['prores'] = True
    if config['dnxhd']:
        post_hook_options['dnxhd'] = True
    post_hook_options = json.dumps(post_hook_options)

    params = []
    if project_type == "mayaproject":
        params.append(('project_directory', config["project_directory"]))
        file_label = "project_file"
    elif project_type == "aftereffectsproject":
        params.append(('render_queue_index',config["render_queue_index"]))
        file_label = "project_file"
    elif project_type == "blenderscene":
        file_label = "scene_file"
    
    params.extend([('csrfmiddlewaretoken', csrftoken),
              ('tasks-job-content_type-object_id-TOTAL_FORMS', '1'),
              ('tasks-job-content_type-object_id-INITIAL_FORMS', '0'),
              ('tasks-job-content_type-object_id-0-status', '0'),
              ('tasks-job-content_type-object_id-0-priority', '50'),
              ('tasks-job-content_type-object_id-0-pool', '1'),
              ('tasks-job-content_type-object_id-0-post_hook', post_hook),
              ('tasks-job-content_type-object_id-0-post_hook_options', post_hook_options),
              (file_label, relative_path()),
              ('block_size', config['block_size']),
              ('frame_start', frame_start),
              ('frame_end', frame_end),
              ('_save', 'Save')])        
    
    params = urlencode(params)
    if sys.version_info[0] >= 3:
        params = params.encode("ascii")    
    
    page = urlopen.open(add_url, params)
    content = page.read()
    
    if sys.version_info[0] >= 3:
        content = content.decode("utf-8")
        
    if 'added successfully' not in content:
        ret = message('Job submission failed')
        return ret
    else:
        ret = message('Job submission successful')
        return ret

if __name__ == "__main__":
    sys.argv[1] = json.loads(sys.argv[1])
    submit_to_dire(arg for arg in sys.argv[1:])
