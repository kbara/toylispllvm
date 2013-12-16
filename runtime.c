/* Runtime.c: various runtime helper functions for the toy lisp.
Copyright (C) 2013 Kat

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/


#include <stdint.h>
#include <unistd.h>

struct box {
	intptr_t val;
	int type;
};

int32_t add_boxed(struct box *box1, struct box *box2) {
	return box1->val + box2->val;
}

struct box* box_val(intptr_t val, int type) {
	struct box *bmem = malloc(sizeof(struct box));
	if (!bmem) {
		exit(1);
	}
	bmem->val = val;
	bmem->type = type;

	return bmem;
}

/* Convenience, for dealing with LLVM */
struct box* box_ptr(void *val, int type) {
	return box_val(val, type);
}

