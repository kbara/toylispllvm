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

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <assert.h>

#include "runtime.h"

/* TODO: check that boxN->type is int */
int32_t add_boxed(struct box *box1, struct box *box2) {
	assert(box1->data_type == BOX_TYPE);
	assert(box2->data_type == BOX_TYPE);
	return box1->val + box2->val;
}

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

struct lambda* make_lambda(void **fp, int num_args) {
	struct lambda *lmem = malloc(sizeof(struct lambda));
	if (!lmem) {
		exit(1);
	}
	printf("fp is %i, *fp is %i\n", fp, *fp);
	lmem->data_type = LAMBDA_TYPE;
	lmem->function_ptr = *fp;
	lmem->num_args = num_args;
	return lmem;
}

int lambda_num_args(struct lambda *alambda) {
	return alambda->num_args;
}

int lambda_get_fp(struct lambda *alambda) {
	return alambda->function_ptr;
}

struct cons* cons(struct box *val, struct cons *next) {
	struct cons *cmem = malloc(sizeof(struct cons));
	if (!cmem) {
		exit(1);
	}
	cmem->data_type = CONS_TYPE;
	cmem->car = val;
	cmem->cdr = next;

	return cmem;
}

void* head(struct cons* alist) {
	assert(alist != NULL);
	assert(alist->data_type == CONS_TYPE);
	return alist->car;
}

void* tail(struct cons* alist) {
	assert(alist != NULL);
	assert(alist->data_type == CONS_TYPE);
	return alist->cdr;
}

/* Convenience, for testing; arguably, it should check it's TYPE_INT */
int get_int_from_box(struct box* abox) {
	assert(abox->data_type == BOX_TYPE);
	return abox->val;
}
