```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-09636-10456") and reject-phase = false
sort location, company asc
```
