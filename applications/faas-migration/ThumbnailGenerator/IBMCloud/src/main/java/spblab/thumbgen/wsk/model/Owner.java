// Generated Using:
//    http://www.jsonschema2pojo.org/
package spblab.thumbgen.wsk.model;

import java.io.Serializable;
import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class Owner implements Serializable
{

    @SerializedName("DisplayName")
    @Expose
    private String displayName;
    @SerializedName("ID")
    @Expose
    private String iD;
    private final static long serialVersionUID = -8310962428768193867L;

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public String getID() {
        return iD;
    }

    public void setID(String iD) {
        this.iD = iD;
    }

    @Override
    public String toString() {
        return new ToStringBuilder(this).append("displayName", displayName).append("iD", iD).toString();
    }

    @Override
    public int hashCode() {
        return new HashCodeBuilder().append(displayName).append(iD).toHashCode();
    }

    @Override
    public boolean equals(Object other) {
        if (other == this) {
            return true;
        }
        if ((other instanceof Owner) == false) {
            return false;
        }
        Owner rhs = ((Owner) other);
        return new EqualsBuilder().append(displayName, rhs.displayName).append(iD, rhs.iD).isEquals();
    }

}
