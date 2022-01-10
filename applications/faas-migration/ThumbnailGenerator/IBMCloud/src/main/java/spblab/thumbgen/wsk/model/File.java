// Generated Using:
//    http://www.jsonschema2pojo.org/
package spblab.thumbgen.wsk.model;

import java.io.Serializable;

import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class File implements Serializable {

    @SerializedName("ETag")
    @Expose
    private String eTag;
    @SerializedName("Key")
    @Expose
    private String key;
    @SerializedName("LastModified")
    @Expose
    private String lastModified;
    @SerializedName("Owner")
    @Expose
    private Owner owner;
    @SerializedName("Size")
    @Expose
    private Long size;
    @SerializedName("StorageClass")
    @Expose
    private String storageClass;
    private final static long serialVersionUID = -1162527747218183698L;

    public String getETag() {
        return eTag;
    }

    public void setETag(String eTag) {
        this.eTag = eTag;
    }

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getLastModified() {
        return lastModified;
    }

    public void setLastModified(String lastModified) {
        this.lastModified = lastModified;
    }

    public Owner getOwner() {
        return owner;
    }

    public void setOwner(Owner owner) {
        this.owner = owner;
    }

    public Long getSize() {
        return size;
    }

    public void setSize(Long size) {
        this.size = size;
    }

    public String getStorageClass() {
        return storageClass;
    }

    public void setStorageClass(String storageClass) {
        this.storageClass = storageClass;
    }

    @Override
    public String toString() {
        return new ToStringBuilder(this).append("eTag", eTag).append("key", key).append("lastModified", lastModified).append("owner", owner).append("size", size).append("storageClass", storageClass).toString();
    }

    @Override
    public int hashCode() {
        return new HashCodeBuilder().append(eTag).append(storageClass).append(lastModified).append(owner).append(key).append(size).toHashCode();
    }

    @Override
    public boolean equals(Object other) {
        if (other == this) {
            return true;
        }
        if ((other instanceof File) == false) {
            return false;
        }
        File rhs = ((File) other);
        return new EqualsBuilder().append(eTag, rhs.eTag).append(storageClass, rhs.storageClass).append(lastModified, rhs.lastModified).append(owner, rhs.owner).append(key, rhs.key).append(size, rhs.size).isEquals();
    }
}
