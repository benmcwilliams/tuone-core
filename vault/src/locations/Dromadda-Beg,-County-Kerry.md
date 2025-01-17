```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Dromadda Beg, County Kerry"
sort company, dt_announce desc
```
