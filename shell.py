# encoding: utf-8

import sublime, sublime_plugin
import os, subprocess

_panel = aliases = cdir = out = window = None

def plugin_loaded():
    global aliases
    settings = sublime.load_settings('Shell.sublime-settings')
    aliases = settings.get('aliases')

class ShellInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, pos, msg):
        self.view.insert(edit, pos, msg)

class ShellReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, pos, msg):
        self.view.replace(edit, self.view.line(pos), msg)

class SublimeShellCommand(sublime_plugin.TextCommand):
    def run(self, edit, panel=False):
        global _panel, cdir, out, window
        _panel = panel
        if window is None:
            window = self.view.window()
        if cdir is None:
            fname = self.view.file_name()
            cdir = os.path.dirname(fname)
        try:
            os.chdir(cdir)
        except OSError:
            os.chdir('E:')
        if _panel:
            out = window.get_output_panel('shell')
        if out is None:
            out = window.new_file()
            out.set_name('*Shell Output*')
            out.set_scratch(True)
            out.settings().set('word_wrap', True)
            grp, _idx = window.get_view_index(out)
            code = window.views_in_group(grp)[max(0, _idx - 1)]
            idx = len(window.views_in_group(grp + 1))
            window.set_view_index(out, grp + 1, idx)
            window.focus_view(code)
            window.focus_view(out)
        out.run_command(
            'shell_insert', {
                'pos': out.size(),
                'msg': '[%s]\n$ ' % cdir
            }
        )
        window.show_input_panel('[Enter a Command]  █', '', self.on_done, self.on_change, None)

    def on_change(self, user_input):
        out.run_command(
            'shell_replace', {
                'pos': out.size(),
                'msg': '$ %s' % user_input
            }
        )

    def on_done(self, user_input):
        global cdir, out, window
        user_input = ' '.join(aliases.get(cmd, cmd) for cmd in user_input.split())
        if user_input == 'exit':
            out.run_command(
                'shell_insert', {
                    'pos': out.size(),
                    'msg': '\n\n*Shell Closed*\n'
                }
            )
            cdir = out = window = None
            return
        if user_input.startswith('cd'):
            try:
                os.chdir(user_input[2: ].strip())
                cdir = os.getcwd()
                msg = ''
            except OSError:
                msg = 'The system cannot find the path specified.\n'
        else:
            pipe = subprocess.Popen(
                user_input,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                shell=True,
                universal_newlines=True
            )
            msg = pipe.stdout.read() + pipe.stderr.read()
        out.run_command(
            'shell_insert', {
                'pos': out.size(),
                'msg': '\n' + msg + '\n'
            }
        )
        out.show(out.size())
        if _panel:
            window.run_command('show_panel', {'panel': 'output.shell'})
        else:
            out.run_command('sublime_shell')
