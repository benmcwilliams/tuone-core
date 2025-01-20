```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "FRA-02239-02186") and reject-phase = false
sort location, company asc
```
