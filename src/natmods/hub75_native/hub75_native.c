#include "py/dynruntime.h"

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY;
    // no exports yet
    MP_DYNRUNTIME_INIT_EXIT;
}
