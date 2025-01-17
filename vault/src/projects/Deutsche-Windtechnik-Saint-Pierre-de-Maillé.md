```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-07116-07675") and reject-phase = false
sort location, company asc
```
