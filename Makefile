test: lispruntime.so.0
	python test_exec.py
	python test_parse.py

lispruntime.so.0: runtime.c
	gcc -Werror -shared -Wl,-soname,lispruntime.so.0 -o lisp_runtime.so.0.0.1 -fPIC -rdynamic -export-dynamic runtime.c

clean:
	rm -f lisp_runtime.so*


