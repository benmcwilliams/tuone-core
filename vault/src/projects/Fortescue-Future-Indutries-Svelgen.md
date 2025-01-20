```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "NOR-04646-02237") and reject-phase = false
sort location, company asc
```
