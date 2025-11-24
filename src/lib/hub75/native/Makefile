SRC = native.c
ARCHES := armv7emsp armv6m
MOD = $(ARCH)
BUILD := ./build

# Link with libgcc.a for division helper functions
LINK_RUNTIME := $(if $(filter armv6m,$(ARCH)),1,)

ifdef ARCH

include $(MPY_DIR)/py/dynruntime.mk

# Windows fix: realpath doesn't handle spaces in paths correctly
# Override library paths if they're empty (Windows issue)
ifeq ($(LIBGCC_PATH),)
LIBGCC_FILE := $(shell $(CROSS)gcc $(CFLAGS) --print-libgcc-file-name)
LIBM_FILE := $(shell $(CROSS)gcc $(CFLAGS) --print-file-name=libm.a)
ifneq ($(LIBGCC_FILE),)
MPY_LD_FLAGS = -l "$(LIBGCC_FILE)" -l "$(LIBM_FILE)"
endif
endif

else

.PHONY: all $(ARCHES)

all: $(ARCHES)

$(ARCHES):
	$(MAKE) ARCH=$@ BUILD=$(BUILD)/$@

endif