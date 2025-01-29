```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-00268-00440") and reject-phase = False
sort location, company asc
```
