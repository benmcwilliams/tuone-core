```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-02043-05271") and reject-phase = false
sort location, company asc
```
