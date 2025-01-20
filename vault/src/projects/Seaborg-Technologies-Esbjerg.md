```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DNK-02098-09967") and reject-phase = false
sort location, company asc
```
