```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-00657-02504") and reject-phase = false
sort location, company asc
```
