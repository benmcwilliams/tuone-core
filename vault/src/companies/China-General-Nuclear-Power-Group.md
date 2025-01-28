```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "China-General-Nuclear-Power-Group" or company = "China General Nuclear Power Group")
sort location, dt_announce desc
```
