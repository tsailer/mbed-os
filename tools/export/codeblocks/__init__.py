"""
mbed SDK
Copyright (c) 2014-2017 ARM Limited
Copyright (c) 2018 Code::Blocks

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import copy
import os
from os.path import splitext, basename
from os import remove
from shutil import rmtree
from tools.targets import TARGET_MAP
from tools.export.exporters import Exporter
from tools.export.makefile import GccArm

class CodeBlocks(GccArm):
    NAME = 'Code::Blocks'

    DOT_IN_RELATIVE_PATH = True

    MBED_CONFIG_HEADER_SUPPORTED = True

    PREPROCESS_ASM = False

    POST_BINARY_WHITELIST = set([
        "NCS36510TargetCode.ncs36510_addfib"
    ])

    @classmethod
    def is_target_supported(cls, target_name):
        target = TARGET_MAP[target_name]
        return apply_supported_whitelist(
            cls.TOOLCHAIN, cls.POST_BINARY_WHITELIST, target)

    @staticmethod
    def filter_dot(str_in):
        """
        Remove the './' prefix, if present.
        This function assumes that resources.win_to_unix()
        replaced all windows backslashes with slashes.
        """
        if str_in is None:
            return None
        if str_in[:2] == './':
            return str_in[2:]
        return str_in

    def generate(self):
        self.resources.win_to_unix()

        comp_flags = []
        debug_flags = []
        next_is_include = False
        for f in self.flags['c_flags'] + self.flags['cxx_flags'] + self.flags['common_flags']:
            f=f.strip()
            if f == "-include":
                next_is_include = True
                continue
            if f == 'c':
                continue
            if next_is_include:
                f = '-include ' + f
            next_is_include = False
            if f.startswith('-O') or f.startswith('-g'):
                debug_flags.append(f)
                continue
            comp_flags.append(f)
        comp_flags = list(set(comp_flags))
        inc_dirs = [self.filter_dot(s) for s in self.resources.inc_dirs];
        inc_dirs = [x for x in inc_dirs if x is not None and x != '' and x != '.' and not x.startswith('bin') and not x.startswith('obj')];

        c_sources = [self.filter_dot(s) for s in self.resources.c_sources]
        ncs36510fib = hasattr(target, "post_binary_hook") and getattr(target, "post_binary_hook") == 'NCS36510TargetCode.ncs36510_addfib'
        if ncs36510fib:
            c_soures.append('ncs36510fib.c')
            c_soures.append('ncs36510trim.c')

        ctx = {
            'project_name': self.project_name,
            'debug_flags': debug_flags,
            'comp_flags': comp_flags,
            'ld_flags': self.flags['ld_flags'],
            'headers': list(set([self.filter_dot(s) for s in self.resources.headers])),
            'c_sources': c_sources,
            's_sources': [self.filter_dot(s) for s in self.resources.s_sources],
            'cpp_sources': [self.filter_dot(s) for s in self.resources.cpp_sources],
            'include_paths': inc_dirs,
            'linker_script': self.filter_dot(self.resources.linker_script),
            'libraries': self.resources.libraries
            }

        self.gen_file('codeblocks/cbp.tmpl', ctx, "%s.%s" % (self.project_name, 'cbp'))
        if ncs36510fib:
            for f in [ 'ncs36510fib.c', 'ncs36510trim.c' ]:
                self.gen_file("codeblocks/%s" % f, ctx, f)

        # finally, generate the Makefile
        super(CodeBlocks, self).generate()

    @staticmethod
    def clean(project_name):
        for ext in ['cbp', 'depend', 'layout']:
            remove("%s.%s" % (project_name, ext))
        remove('openocd.log')
        remove('ncs36510fib.c')
        remove('ncs36510trim.c')
        rmtree('bin', ignore_errors=True)
        rmtree('obj', ignore_errors=True)
