{% macro postgres__log_transform(column, base, offset)  %}

    case
        when {{ column }} is null or {{ column }} + {{ offset }} <= 0 then null
        else log({{ base }}::numeric, ({{ column }} + {{ offset }})::numeric)
    end

{% endmacro %}