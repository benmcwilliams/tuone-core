```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-04583-05904") and reject-phase = false
sort location, company asc
```
