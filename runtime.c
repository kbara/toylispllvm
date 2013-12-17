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
#include <stdlib.h>
#include <assert.h>

typedef intptr_t lispval_t; /* Consider changing this to be 128-bit for quadfloats */

#define CONS_TYPE 0x636f6e73 /* "cons" */
#define BOX_TYPE 0x626f78 /* "box" */

struct box {
	int data_type;
	lispval_t val;
	int type;
};

struct cons {
	int data_type;
	struct box *val;
	struct cons *next;
};

/* TODO: check that boxN->type is int */
int32_t add_boxed(struct box *box1, struct box *box2) {
	assert(box1->data_type == BOX_TYPE);
	assert(box2->data_type == BOX_TYPE);
	return box1->val + box2->val;
}
/*
int32_t mul_boxed(struct box *box1, struct box *box2) {
        assert(box1->data_type == BOX_TYPE);
        assert(box2->data_type == BOX_TYPE);
        return box1->val * box2->val;
}

int32_t sub_boxed(struct box *box1, struct box *box2) {
        assert(box1->data_type == BOX_TYPE);
        assert(box2->data_type == BOX_TYPE);
        return box1->val - box2->val;
}*/

struct box* box_val(lispval_t val, int type) {
	struct box *bmem = malloc(sizeof(struct box));
	if (!bmem) {
		exit(1);
	}
	bmem->data_type = BOX_TYPE;
	bmem->val = val;
	bmem->type = type;

	return bmem;
}

/* Convenience, for dealing with LLVM */
struct box* box_ptr(void *val, int type) {
	return box_val((lispval_t) val, type);
}

struct cons* cons(struct box *val, struct cons *next) {
	struct cons *cmem = malloc(sizeof(struct cons));
	if (!cmem) {
		exit(1);
	}
	cmem->data_type = CONS_TYPE;
	cmem->val = val;
	cmem->next = next;

	return cmem;
}

struct box* head(struct cons* alist){
	assert(alist != NULL);
	assert(alist->data_type == CONS_TYPE);
	return alist->val;
}

/* Convenience, for testing; arguably, it should check it's TYPE_INT */
int get_int_from_box(struct box* abox) {
	assert(abox->data_type == BOX_TYPE);
	return abox->val;
}
