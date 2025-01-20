```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "IRL-01896-01695") and reject-phase = false
sort location, company asc
```
