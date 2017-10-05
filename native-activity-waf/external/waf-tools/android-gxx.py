###############################################################################
 #
 # Oak game engine
 # Copyright (c) 2013 Remi Papillie
 #
 # Permission is hereby granted, free of charge, to any person obtaining a
 # copy of this software and associated documentation files (the "Software"),
 # to deal in the Software without restriction, including without limitation
 # the rights to use, copy, modify, merge, publish, distribute, sublicense,
 # and/or sell copies of the Software, and to permit persons to whom the
 # Software is furnished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 # THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 # DEALINGS IN THE SOFTWARE.
 # 
###############################################################################

#! /usr/bin/env python
# encoding: utf-8

import os, sys, glob
from waflib import Configure,Options,Utils
from waflib.Tools import ccroot,ar
from waflib.Configure import conf

def options(ctx):
	group = ctx.add_option_group("android-specific config")
	group.add_option("--ndk", action = "store", default = os.getenv("ANDROID_NDK_ROOT"), help = "Android NDK root")

@conf
def find_android_gxx(conf):
	exeDir = os.path.join(conf.options.ndk, "toolchains", "llvm", "prebuilt", "*", "bin")
	exeDir = glob.glob(exeDir)

	cxx=conf.find_program(['clang++'], var = "CXX", path_list=exeDir)
	cxx=conf.cmd_to_list(cxx)
	conf.get_cc_version(cxx, clang=True)
	conf.env.CXX_NAME='clang'
	conf.env.CXX=cxx

@conf
def android_gxx_common_flags(conf):
	v=conf.env
	v['CXX_SRC_F']=[]
	v['CXX_TGT_F']=['-c','-o']
	if not v['LINK_CXX']:v['LINK_CXX']=v['CXX']
	v['CXXLNK_SRC_F']=[]
	v['CXXLNK_TGT_F']=['-o']
	v['CPPPATH_ST']='-I%s'
	v['DEFINES_ST']='-D%s'
	v['LIB_ST']='-l%s'
	v['LIBPATH_ST']='-L%s'
	v['STLIB_ST']='-l%s'
	v['STLIBPATH_ST']='-L%s'
	v['RPATH_ST']='-Wl,-rpath,%s'
	v['SONAME_ST']='-Wl,-h,%s'
	v['SHLIB_MARKER']='-Wl,-Bdynamic'
	v['STLIB_MARKER']='-Wl,-Bstatic'
	v['cxxprogram_PATTERN']='%s'
	v['CXXFLAGS_cxxshlib']=['-fPIC']
	v['LINKFLAGS_cxxshlib']=['-shared']
	v['cxxshlib_PATTERN']='lib%s.so'
	v['LINKFLAGS_cxxstlib']=['-Wl,-Bstatic']
	v['cxxstlib_PATTERN']='lib%s.a'
	v['LINKFLAGS_MACBUNDLE']=['-bundle','-undefined','dynamic_lookup']
	v['CXXFLAGS_MACBUNDLE']=['-fPIC']
	v['macbundle_PATTERN']='%s.bundle'

@conf
def android_gxx_modifier_android9(conf):
	v=conf.env
	v['CXXFLAGS']=[
		"-fPIC",
		"-ffunction-sections",
		"-funwind-tables",
		"-fstack-protector",
		"-mthumb",
		"-Os",
		"-fomit-frame-pointer",
		"-fno-strict-aliasing",
		"-DANDROID"
	]

	v.TARGET_ARCH = 'armv7'

	gcc_toolchain_dir = os.path.join(conf.options.ndk, "toolchains", "arm-linux-androideabi-*", "prebuilt", "*")
	gcc_toolchain_dir = glob.glob(gcc_toolchain_dir)[0]
	
	if v.TARGET_ARCH == "armv6":
		v.append_unique('CXXFLAGS', [
			"-march=armv5te",
			"-mtune=xscale",
			"-msoft-float"
		])
	elif v.TARGET_ARCH == "armv7":
		v.append_unique('CXXFLAGS', [
			"-target", "armv7-none-linux-androideabi",
			"-gcc-toolchain", gcc_toolchain_dir,
			"-march=armv7-a",
			"-mfloat-abi=softfp",
			"-mfpu=vfpv3-d16"
		])
		v.append_unique('LINKFLAGS', [
			"-target", "armv7-none-linux-androideabi",
			"-gcc-toolchain", gcc_toolchain_dir,
			"-march=armv7-a",
			"-Wl,--fix-cortex-a8"
		])
	
	android_arch = "arm"
	if conf.env.TARGET_ARCH == "mips":
		android_arch = "mips"
	elif conf.env.TARGET_ARCH == "x86":
		android_arch = "x86"
	
	platform = 'android-23'

	sysroot = os.path.join(conf.options.ndk, "platforms/%s/arch-%s" % (platform, android_arch))
	v.append_unique('CXXFLAGS', ["--sysroot=" + sysroot])
	v.append_unique('LINKFLAGS', ["--sysroot=" + sysroot])
	
	v.append_unique('INCLUDES', [os.path.join(conf.options.ndk, 'sources/cxx-stl/llvm-libc++/include')])
	v.append_unique('INCLUDES', [os.path.join(conf.options.ndk, 'sources/cxx-stl/llvm-libc++/libcxx/include')])
	v.append_unique('INCLUDES', [os.path.join(conf.options.ndk, 'sources/cxx-stl/llvm-libc++/libs/armeabi-v7a/include')])
	v.append_unique('INCLUDES', [os.path.join(conf.options.ndk, 'sources/android/native_app_glue/')])
	v.append_unique('INCLUDES', [os.path.join(conf.options.ndk, 'sources/android/support/include/')])

	v.append_unique('LIBPATH', [os.path.join(conf.options.ndk, 'sources/cxx-stl/llvm-libc++/libs/armeabi-v7a')])
	v.append_unique('LIB', ["c++_shared", "m", "dl", "android", "log", "GLESv2", "EGL"]) # "gnustl_static",
	
	# save NDK path for later steps
	v.NDK_ROOT = conf.options.ndk
	v.GCC_TOOLCHAIN_DIR = gcc_toolchain_dir

@conf
def android_gxx_modifier_platform(conf):
	# android_gxx_modifier_func=getattr(conf,'android_gxx_modifier_'+conf.env.TARGET_OS,None)
	android_gxx_modifier_func=getattr(conf, 'android_gxx_modifier_android9', None)
	if android_gxx_modifier_func:
		android_gxx_modifier_func()

def configure(conf):
	# Check that the NDK path was given on the command-line
	conf.msg("NDK path configured with --ndk", conf.options.ndk != None)
	if not conf.options.ndk:
		raise "no NDK path"
	
	conf.load('android-gcc', tooldir="waf-tools")
	conf.find_android_gxx()
	# conf.load('android-ar', tooldir="waf-tools")
	conf.android_gxx_common_flags()
	conf.android_gxx_modifier_platform()
	conf.cxx_load_tools()
	conf.cxx_add_flags()
	conf.link_add_flags()
