```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-08739-02328") and reject-phase = false
sort location, company asc
```
