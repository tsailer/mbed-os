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

    def generate(self):
        self.resources.win_to_unix()

        sources         = [] # list of strings

        for r_type in ['headers', 'c_sources', 's_sources', 'cpp_sources']:
            sources.extend(getattr(self.resources, r_type))

        comp_flags = []
        debug_flags = []
        next_is_include = False
        for f in self.flags['c_flags'] + self.flags['cxx_flags'] + self.flags['common_flags']:
            f=f.strip()
            if f == "-include":
                next_is_include = True
                continue
            if next_is_include:
                f = '-include ' + f
            next_is_include = False
            if f.startswith('-O') or f.startswith('-g'):
                debug_flags.append(f)
                continue
            comp_flags.append(f)
        comp_flags = list(set(comp_flags))

        ctx = {
            'project_name': self.project_name,
            'debug_flags': debug_flags,
            'comp_flags': comp_flags,
            'ld_flags': self.flags['ld_flags'],
            'headers': list(set(self.resources.headers)),
            'c_sources': self.resources.c_sources,
            's_sources': self.resources.s_sources,
            'cpp_sources': self.resources.cpp_sources,
            'sources': sources,
            'include_paths': self.resources.inc_dirs,
            'linker_script': self.resources.linker_script,
            'libraries': self.resources.libraries
            }

        self.gen_file('codeblocks/cbp.tmpl', ctx, "%s.%s" % (self.project_name, 'cbp'))

        # finally, generate the Makefile
        super(CodeBlocks, self).generate()

    @staticmethod
    def clean(project_name):
        for ext in ['cbp', 'depend', 'layout']:
            remove("%s.%s" % (project_name, ext))
        remove('openocd.log')
        rmtree('bin', ignore_errors=True)
        rmtree('obj', ignore_errors=True)
