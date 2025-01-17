```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-08543-08744") and reject-phase = false
sort location, company asc
```
