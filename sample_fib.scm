(let
 ((in 11)
  (result 1)
  (prev 0)
  (tmp 0))
 (if (= in 0)
  0
  (begin
   (while
    (< 1 in)
    (begin
     (set! tmp result)
     (set! result (+ result prev))
     (set! prev tmp)
     (set! in (+ in -1))
    )
   )
   result
  )
 )
)
