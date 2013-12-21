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

#ifndef __RUNTIME_H
#define __RUNTIME_H
#include "runtime.h"

typedef intptr_t lispval_t;

#define CONS_TYPE 0x636f6e73 /* "cons" */
#define BOX_TYPE 0x626f78 /* "box" */
#define LAMBDA_TYPE 0x6c6d6264 /* "lmda" */

struct box {
	int data_type;
	lispval_t val;
	int type;
};

struct cons {
	int data_type;
	void *car;
	void *cdr;
};

struct lambda {
	int data_type;
	void *function_ptr;
	int num_args;
};

int32_t add_boxed(struct box *box1, struct box *box2);
struct box* box_val(lispval_t val, int type);
struct box* box_ptr(void *val, int type);

struct lambda* make_lambda(void **fp, int num_args);
int lambda_num_args(struct lambda *alambda);
void* lambda_get_fp(struct lambda *alambda);

struct cons* cons(struct box *val, struct cons *next);
void* head(struct cons* alist);
void* tail(struct cons* alist);

/* Convenience, for testing; arguably, it should check it's TYPE_INT */
int get_int_from_box(struct box* abox);

#endif
