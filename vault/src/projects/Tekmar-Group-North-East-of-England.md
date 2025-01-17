```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-10079-10207") and reject-phase = false
sort location, company asc
```
