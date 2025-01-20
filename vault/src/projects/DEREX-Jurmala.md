```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "LVA-08371-08585") and reject-phase = false
sort location, company asc
```
