# 交叉编译 Linux 内核驱动
# 使用方式：
#   make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- KDIR=/path/to/kernel

KDIR ?= /lib/modules/$(shell uname -r)/build
ARCH ?= arm64
CROSS_COMPILE ?= aarch64-linux-gnu-

all:
	$(MAKE) -C $(KDIR) M=$(PWD) \
		ARCH=$(ARCH) \
		CROSS_COMPILE=$(CROSS_COMPILE) \
		modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# PetaLinux 内嵌驱动方式
# 在 project-spec/meta-user/recipes-modules/ 下创建 bbappend
# 或直接将源码放入 kernel/drivers/media/platform/
install:
	$(MAKE) -C $(KDIR) M=$(PWD) \
		ARCH=$(ARCH) \
		CROSS_COMPILE=$(CROSS_COMPILE) \
		modules_install INSTALL_MOD_PATH=$(DESTDIR)
