```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-04302-05935") and reject-phase = false
sort location, company asc
```
